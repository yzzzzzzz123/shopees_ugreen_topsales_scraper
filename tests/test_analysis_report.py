"""验证真实计算、缺口、来源绑定与 PDF 原子交付；不访问网页。"""
from contextlib import nullcontext
from datetime import date, timedelta
from decimal import Decimal as D
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / "skills/shopee-ugreen-topsales/scripts"
sys.path.insert(0,str(SCRIPTS))
import analysis_report as report
import excel
import publish_result
from test_publish_result import fixture


def product(item, monthly, price="100", shop="64922227"):
    return report.Product(shop,str(item),int(item),f"商品 {item}",f"https://shopee.ph/product/{shop}/{item}",
                          D(price),monthly,None if monthly is None else f"{monthly} Sold/Month")


def snapshot(day, *products):
    return report.Snapshot(day,Path(f"/snapshots/{day:%Y%m%d}_ugreen_topsales/result/ugreen_topsales.xlsx"),
                           "a"*64,day.strftime("%Y/%m/%d 12:00:00"),{p.key:p for p in products})


class MetricTests(unittest.TestCase):
    def setUp(self):
        self.day=date(2026,9,23)

    def test_matched_ids_missing_sales_and_zero_base_are_distinct(self):
        before=snapshot(self.day-timedelta(days=1),product(1,10,"100"),product(2,0,"0"),product(3,None),product(4,8),product(9,50))
        now=snapshot(self.day,product(1,12,"90"),product(2,3,"20"),product(3,0),product(4,8),product(5,100))
        self.assertEqual(report.movement(now,before,"monthly"),dict(up=2,down=0,flat=1,unknown=1,common=4))
        self.assertEqual(report.movement(now,before,"price"),dict(up=1,down=1,flat=2,unknown=0,common=4))
        self.assertEqual(report.delta(12,10),(D(2),D(20)))
        self.assertEqual(report.delta(D("90"),D("100")),(D(-10),D(-10)))
        self.assertEqual(report.delta(3,0),(D(3),None))
        self.assertEqual(report.delta(0,None),(None,None))

    def test_store_identity_is_part_of_join(self):
        now=snapshot(self.day,product(1,20))
        previous=snapshot(self.day-timedelta(days=1),product(1,10,shop="different"))
        self.assertEqual(report.movement(now,previous,"monthly")["common"],0)

    def test_baseline_gap_and_returning_links(self):
        d=self.day
        old=snapshot(d-timedelta(days=2),product(1,10),product(2,10))
        previous=snapshot(d-timedelta(days=1),product(1,10),product(4,2))
        now=snapshot(d,product(1,11),product(2,9),product(3,1))
        self.assertIsNone(report.listing_changes(d,{d:now})["added"])
        self.assertIsNone(report.listing_changes(d,{old.day:old,d:now})["added"])
        result=report.listing_changes(d,{old.day:old,previous.day:previous,d:now})
        self.assertEqual([result[k] for k in ("added","first_seen","returned","missing")],[2,1,1,1])

    def test_fixed_price_boundaries_and_amount_reconcile(self):
        prices=("0","99.99","100","299.99","300","499.99","500","999.99","1000","1999.99","2000","4999.99","5000")
        now=snapshot(self.day,*(product(i+1,2,p) for i,p in enumerate(prices)),product(99,None,"100"))
        bands=report.price_bands(now)
        self.assertEqual([b["links"] for b in bands],[2,3,2,2,2,2,1])
        total=report.totals(now)
        self.assertEqual(sum(b["links"] for b in bands),total["links"])
        self.assertEqual(sum(b["volume"] for b in bands),26)
        self.assertEqual(sum(b["amount"] for b in bands),total["amount"])
        self.assertAlmostEqual(sum(b["share"] for b in bands),D(100))
        self.assertEqual(total["weighted_price"],sum(map(D,prices))/13)
        self.assertEqual(total["missing"],1)

    def test_all_unknown_is_not_zero_or_inactive(self):
        now=snapshot(self.day,product(1,None))
        result=report.totals(now)
        self.assertIsNone(result["volume"])
        self.assertIsNone(result["amount"])
        self.assertIsNone(result["weighted_price"])
        self.assertEqual(result["zero"],0)
        self.assertIsNone(report.price_bands(now)[1]["volume"])

    def test_known_zero_has_zero_amount_and_undefined_weighted_price(self):
        result=report.totals(snapshot(self.day,product(1,0)))
        self.assertEqual(result["volume"],0)
        self.assertEqual(result["amount"],0)
        self.assertIsNone(result["weighted_price"])

    def test_month_suffix_does_not_count_as_rounded_million_prefix(self):
        ordinary=product(1,12)
        rounded=report.Product("64922227","2",2,"产品2","https://shopee.ph/product/64922227/2",D(20),1200,"1.2K+ Sold/Month")
        self.assertEqual(report.totals(snapshot(self.day,ordinary,rounded))["rounded"],1)

    def test_calendar_windows_and_gap_preservation(self):
        days=report.days_ending(date(2026,3,1),7)
        self.assertEqual(days[0],date(2026,2,23))
        self.assertEqual(days[-1],date(2026,3,1))
        self.assertEqual(report.sparkline([None,0,None,10]),"·▁·█")
        self.assertEqual(report.sparkline([None,None]),"··")
        chart=report.trend_chart(days,[None]*6+[10],"测试")
        self.assertEqual(chart.count("●"),2)  # 一个真实观测点和一个图例符号
        self.assertIn("有效观测不足 2 天",chart)

    def test_report_is_deterministic_escapes_titles_and_keeps_baseline_unknown(self):
        malicious=report.Product("64922227","1",1,"<script>x</script>|\n[假](javascript:x)",
                                 "https://shopee.ph/product/64922227/1",D(20),None,None)
        now=snapshot(self.day,malicious)
        content=report.render_report(now,{self.day:now},[])
        self.assertEqual(content,report.render_report(now,{self.day:now},[]))
        self.assertNotIn("<script>",content)
        self.assertIn("&lt;script&gt;",content)
        self.assertIn("&#124;",content)
        self.assertIn("新增、首次观察和重新出现数量均不可判定",content)
        self.assertIn("零月销 / 未知链接 | 0 / 0 / 1",content)

    def test_pdf_preserves_literal_title_symbols_and_clickable_link(self):
        from io import BytesIO
        from pypdf import PdfReader
        from analysis_pdf import render_pdf
        title='中文 **USB** `C` <script> | ✨⚡'
        item=report.Product('64922227','1',1,title,'https://shopee.ph/product/64922227/1',D(20),5,'5 Sold/Month')
        now=snapshot(self.day,item)
        pdf=PdfReader(BytesIO(render_pdf(report.render_report(now,{self.day:now},[]))))
        text=''.join(page.extract_text() for page in pdf.pages)
        self.assertIn(title,text)
        links=[a.get_object().get('/A',{}).get('/URI') for p in pdf.pages for a in p.get('/Annots',[])]
        self.assertIn(item.url,links)


class WorkbookReportTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.daily=self.root/"worktrees/20000102_ugreen_topsales"
        self.path=self.daily/"result/ugreen_topsales.xlsx"
        self.path.parent.mkdir(parents=True)
        value,_=publish_result._convert(fixture())
        excel.write_excel(value,self.path)
        for target, replacement in (("analysis_report._target_workbook",lambda root,daily:daily/"result/ugreen_topsales.xlsx"),
                                    ("publish_result._exclusive_publish",lambda root:nullcontext())):
            mocked=patch(target,side_effect=replacement)
            mocked.start();self.addCleanup(mocked.stop)

    def test_real_workbook_read_only_generation_and_tamper_detection(self):
        before=report.digest(self.path)
        receipt=report.write_report(self.root,self.daily)
        self.assertEqual(receipt["report_date"],"2000-01-02")
        self.assertFalse(receipt["previous_day_available"])
        self.assertEqual(receipt["monthly_sales_lower_bound"],1200)
        self.assertEqual(D(receipt["estimated_monthly_amount_php"]),D(12600))
        self.assertEqual(report.validate_report(self.root,self.daily)["analysis_status"],"通过")
        self.assertEqual(report.digest(self.path),before)
        path=self.path.with_name(report.REPORT_NAME)
        self.assertEqual(set(p.name for p in self.path.parent.iterdir()),{self.path.name,report.REPORT_NAME})
        first=path.read_bytes()
        self.assertEqual(report.write_report(self.root,self.daily)["sha256"],receipt["sha256"])
        self.assertEqual(path.read_bytes(),first)
        path.write_bytes(path.read_bytes()+b"unauthorized edit")
        with self.assertRaisesRegex(ValueError,"不一致"):
            report.validate_report(self.root,self.daily)

    def test_unknown_file_not_overwritten_and_temporary_is_cleaned_on_failure(self):
        path=self.path.with_name(report.REPORT_NAME)
        path.write_text("用户已有报告",encoding="utf-8")
        with self.assertRaisesRegex(ValueError,"保留原文件"):
            report.write_report(self.root,self.daily)
        self.assertEqual(path.read_text(encoding="utf-8"),"用户已有报告")
        path.unlink()
        with patch("analysis_report.os.replace",side_effect=OSError("模拟替换失败")):
            with self.assertRaises(OSError):report.write_report(self.root,self.daily)
        self.assertEqual(list(self.path.parent.iterdir()),[self.path])

    def test_partial_or_corrupt_history_is_excluded_not_used_as_yesterday(self):
        older=self.daily.with_name("20000101_ugreen_topsales")/"result/ugreen_topsales.xlsx"
        older.parent.mkdir(parents=True)
        older.write_bytes(b"not a complete workbook")
        now,history,excluded=report.load_history(self.root,self.daily)
        self.assertEqual(list(history),[now.day])
        self.assertEqual(len(excluded),1)


if __name__=="__main__":
    unittest.main()
