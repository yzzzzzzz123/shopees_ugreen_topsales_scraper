"""每日分析的确定性 PDF 排版。中间 Markdown 仅留内存，不另存旁路报告。"""
from __future__ import annotations

from collections import Counter
from functools import lru_cache
import hashlib
import html
from io import BytesIO
import os
from pathlib import Path
import re
import unicodedata

from pypdf import PdfReader
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, PageBreak, CondPageBreak, LongTable, TableStyle, Flowable

PDF_MARKER = 'ugreen-daily-analysis:pdf-v1'
PAGE_W, PAGE_H = landscape(A4)
MARGIN = 36
WIDTH = PAGE_W - 2*MARGIN
GREEN = colors.HexColor('#156747')
INK = colors.HexColor('#25352f')


def _font_file(variable, names):
    if os.environ.get(variable):
        path = Path(os.environ[variable])
        if not path.is_file():
            raise ValueError(f'{variable} 不是可读字体文件')
        return path
    for directory in ('C:/Windows/Fonts', '/mnt/c/Windows/Fonts', '/usr/share/fonts/truetype/dejavu', '/usr/share/fonts/truetype/liberation2'):
        for name in names:
            path = Path(directory)/name
            if path.is_file():
                return path
    raise ValueError(f'缺少 PDF 字体，请通过 {variable} 指定本机可用的 TrueType 字体')


@lru_cache(maxsize=1)
def register_fonts():
    fonts = [('ReportCN','UGREEN_PDF_FONT',('msyh.ttc','simhei.ttf')),
             ('ReportBold','UGREEN_PDF_BOLD_FONT',('msyhbd.ttc','simhei.ttf')),
             ('ReportMono','UGREEN_PDF_MONO_FONT',('consola.ttf','DejaVuSansMono.ttf','LiberationMono-Regular.ttf')),
             ('ReportSymbols','UGREEN_PDF_SYMBOL_FONT',('seguisym.ttf','DejaVuSans.ttf'))]
    for name, env, candidates in fonts:
        pdfmetrics.registerFont(TTFont(name,str(_font_file(env,candidates)),subfontIndex=0))
        pdfmetrics.registerFontFamily(name,normal=name,bold=name,italic=name,boldItalic=name)
    pdfmetrics.registerFontFamily('ReportCN',normal='ReportCN',bold='ReportBold',italic='ReportCN',boldItalic='ReportBold')


def plain(text):
    # 商品名中的星号、反引号或转义 HTML 属于文字，不重新解释为标记。
    pieces=[];last=0
    for match in re.finditer(r'<a\s+href="[^"]+">(.*?)</a>|\*\*(.+?)\*\*|`([^`]+)`',text):
        pieces.append(text[last:match.start()]);pieces.append(next(v for v in match.groups() if v is not None));last=match.end()
    pieces.append(text[last:])
    return html.unescape(''.join(pieces)).replace('\ufe0f','').replace('\u2013','-')


def _chars(text):
    text = html.unescape(text).replace('\ufe0f','').replace('\u2013','-')
    out=[]
    for char in text:
        safe=html.escape(char,quote=False)
        if ord(char) not in pdfmetrics.getFont('ReportCN').face.charToGlyph and not char.isspace():
            fallback=next((f for f in ('ReportSymbols','ReportMono') if ord(char) in pdfmetrics.getFont(f).face.charToGlyph),None)
            if fallback is None:
                raise ValueError(f'PDF 字体缺少字符 U+{ord(char):04X}，请配置覆盖该字符的字体')
            safe=f'<font name="{fallback}">{safe}</font>'
        out.append(safe)
    return ''.join(out)


def inline(text):
    out=[]; last=0
    for m in re.finditer(r'<a\s+href="([^"]+)">(.*?)</a>|\*\*(.+?)\*\*|`([^`]+)`',text):
        out.append(_chars(text[last:m.start()]))
        url,anchor,strong,code=m.groups()
        if url is not None:
            if not html.unescape(url).startswith('https://shopee.ph/'):
                raise ValueError('PDF 商品链接不属于已支持的 Shopee PH')
            out.append(f'<link href="{html.escape(html.unescape(url),quote=True)}" color="#12664b">{_chars(anchor)}</link>')
        elif strong is not None:
            out.append('<b>'+_chars(strong)+'</b>')
        else:
            supported=all(ord(c) in pdfmetrics.getFont('ReportMono').face.charToGlyph for c in html.unescape(code))
            out.append('<font name="'+('ReportMono' if supported else 'ReportCN')+'">'+_chars(code)+'</font>')
        last=m.end()
    out.append(_chars(text[last:]))
    return ''.join(out)


class CodeBlock(Flowable):
    def __init__(self,text):
        super().__init__()
        self.lines=text.splitlines(); self.width=WIDTH; self.height=22+13*len(self.lines)
    def draw(self):
        c=self.canv
        c.setFillColor(colors.HexColor('#f3f7f4'))
        c.roundRect(0,0,self.width,self.height,5,fill=1,stroke=0)
        c.setFillColor(INK)
        for n,line in enumerate(self.lines):
            x=13
            for char in line:
                wide=unicodedata.east_asian_width(char) in ('F','W')
                c.setFont('ReportCN' if wide else 'ReportMono',9)
                c.drawString(x,self.height-17-n*13,char)
                x+=5.4*(2 if wide else 1)


class ReportDoc(BaseDocTemplate):
    section='UGREEN 每日经营分析'
    def afterFlowable(self,flowable):
        if isinstance(flowable,Paragraph) and flowable.style.name in ('h1','h2','h3'):
            title=flowable.getPlainText(); level=int(flowable.style.name[1])-1
            key='section_'+hashlib.sha1(title.encode()).hexdigest()
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(title,key,level=level,closed=False)
            if level==1:self.section=title


def _page_start(c,doc):
    c.saveState(); c.setStrokeColor(GREEN); c.setLineWidth(1)
    c.line(MARGIN,PAGE_H-29,PAGE_W-MARGIN,PAGE_H-29)
    c.setFont('ReportCN',7.8); c.setFillColor(colors.HexColor('#66746e'))
    c.drawString(MARGIN,PAGE_H-21,'UGREEN / PH · PHP / '+doc.report_date)
    c.drawRightString(PAGE_W-MARGIN,PAGE_H-21,'每日经营分析'); c.restoreState()


def _page_end(c,doc):
    c.saveState(); c.setStrokeColor(colors.HexColor('#dce5df')); c.setLineWidth(.5)
    c.line(MARGIN,29,PAGE_W-MARGIN,29)
    c.setFont('ReportCN',7.4); c.setFillColor(colors.HexColor('#66746e'))
    c.drawString(MARGIN,17,doc.section)
    c.drawRightString(PAGE_W-MARGIN,17,f'第 {doc.page} 页'); c.restoreState()


def render_pdf(content: str) -> bytes:
    register_fonts()
    styles={}
    for name,size,leading,bold in [('body',9.3,15.2,False),('bullet',9.1,14.8,False),('h1',22,29,True),('h2',14,21,True),('h3',11,17,True),('cell',8.1,11.4,False),('smallcell',7.9,11.1,False),('header',8.1,11.4,True)]:
        styles[name]=ParagraphStyle(name,fontName='ReportBold' if bold else 'ReportCN',fontSize=size,leading=leading,
                                    textColor=colors.white if name=='header' else GREEN if name.startswith('h') else INK,
                                    wordWrap='CJK' if name in ('body','bullet') else 'LTR',
                                    spaceAfter=7 if name in ('body','bullet') else 10 if name.startswith('h') else 0,
                                    spaceBefore=10 if name in ('h2','h3') else 0,keepWithNext=name in ('h1','h2'))
    styles['bullet'].leftIndent=13;styles['bullet'].firstLineIndent=-11
    lines=content.splitlines();story=[];cells=[];i=0
    page_sections={'店铺汇总','固定价格段的出单占比与动销','7 日店铺月销趋势图','30 日新出现链接趋势图（上新代理）','全部产品链接的月销、价格变化与金额估算','全部产品的 7 日 / 30 日月销迷你趋势图','今日新出现链接明细'}
    while i<len(lines):
        line=lines[i];i+=1
        if not line.strip() or line.startswith('<!--'):continue
        if line.startswith('```'):
            block=[]
            while i<len(lines) and not lines[i].startswith('```'):block.append(lines[i]);i+=1
            i+=1;story.extend([CodeBlock('\n'.join(block)),Spacer(1,9)]);continue
        if line.startswith('|'):
            block=[line]
            while i<len(lines) and lines[i].startswith('|'):block.append(lines[i]);i+=1
            rows=[[v.strip() for v in row.strip().strip('|').split('|')] for row in block]
            rows=[r for r in rows if not all(re.fullmatch(r':?-+:?',c.replace(' ','')) for c in r)]
            n=len(rows[0]);cells.extend(plain(c) for row in rows for c in row)
            if not all(len(r)==n for r in rows):raise ValueError('分析表格列数不一致')
            widths={11:[28,184,59,41,43,44,65,46,46,46,68],6:[30,310,58,163,87,92],8:[90,76,90,85,150,90,95,94],7:[120,85,100,80,115,90,180],3:[192,190,388]}.get(n,[WIDTH/n]*n)
            if n==4:widths=[80,128,270,292] if rows[0][-1]=='SHA-256' else [400,110,110,150]
            widths=[w*WIDTH/sum(widths) for w in widths];formatted=[]
            for idx,row in enumerate(rows):
                parts=[inline(c) for c in row]
                if n==11:
                    if idx==0:parts=[c.replace(' PHP','<br/>PHP') for c in parts]
                    else:parts[2]=parts[2].replace(' Sold/Month','<br/>Sold/Month')
                if n==4 and rows[0][-1]=='SHA-256' and idx>0:
                    sha=plain(row[3]);parts[3]='<font name="ReportMono">'+sha[:32]+'<br/>'+sha[32:]+'</font>'
                st=styles['header' if idx==0 else 'smallcell' if n==11 else 'cell']
                formatted.append([Paragraph(c,st) for c in parts])
            table=LongTable(formatted,colWidths=widths,repeatRows=1,hAlign='LEFT',splitByRow=1)
            table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),GREEN),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f3f7f5')]),('VALIGN',(0,0),(-1,-1),'MIDDLE'),('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),('LINEBELOW',(0,0),(-1,-1),.3,colors.HexColor('#dce5df'))]))
            story.extend([table,Spacer(1,12)]);continue
        heading=re.match(r'^(#{1,3}) (.+)',line)
        if heading:
            level=len(heading[1]);title=heading[2]
            if title in page_sections:story.append(PageBreak())
            if level==3:story.append(CondPageBreak(95))
            story.append(Paragraph(inline(title),styles[f'h{level}']));continue
        if line.startswith('- '):story.append(Paragraph('• '+inline(line[2:]),styles['bullet']));continue
        paragraph=[line]
        while i<len(lines) and lines[i].strip() and not re.match(r'^(#|\||```|- |<!--)',lines[i]):paragraph.append(lines[i]);i+=1
        story.append(Paragraph(inline(' '.join(paragraph)),styles['body']))
    output=BytesIO();title=next(line[2:] for line in lines if line.startswith('# '))
    doc=ReportDoc(output,pagesize=(PAGE_W,PAGE_H),title=title,author='UGREEN 经营分析',keywords=PDF_MARKER+';'+hashlib.sha256(content.encode()).hexdigest(),pageCompression=1)
    doc.report_date=re.search(r'\d{4}-\d{2}-\d{2}',title)[0]
    doc.addPageTemplates(PageTemplate(id='report',frames=[Frame(MARGIN,41,WIDTH,PAGE_H-85,leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0)],onPage=_page_start,onPageEnd=_page_end))
    doc.build(story,canvasmaker=lambda *a,**k:Canvas(*a,**{**k,'invariant':1}))
    result=output.getvalue();reader=PdfReader(BytesIO(result))
    flat=re.sub(r'\s+','','\n'.join(p.extract_text() for p in reader.pages))
    if any(re.sub(r'\s+','',cell) not in flat for cell in cells):raise ValueError('PDF 表格回读不完整')
    expected=Counter(html.unescape(u) for u in re.findall(r'<a href="([^"]+)">',content));actual=Counter()
    for page in reader.pages:
        for ann in page.get('/Annots',[]):
            action=ann.get_object().get('/A',{})
            if action.get('/URI'):actual[str(action['/URI'])]+=1
    if any(actual[u]<n for u,n in expected.items()):raise ValueError('PDF 商品链接缺失')
    return result


def check_controlled_pdf(path: Path, legacy_sha256: str | None = None):
    if path.is_symlink() or (path.exists() and not path.is_file()):raise ValueError('分析 PDF 必须是普通文件')
    if not path.exists():return
    data=path.read_bytes()
    try:
        if not data.startswith(b'%PDF-'):raise ValueError('不是 PDF')
        reader=PdfReader(BytesIO(data))
        controlled=str(reader.metadata.get('/Keywords','')).startswith(PDF_MARKER+';') and bool(reader.pages)
    except Exception:
        controlled=False
    if not controlled and (not legacy_sha256 or hashlib.sha256(data).hexdigest()!=legacy_sha256):
        raise ValueError('同名 PDF 不是受控分析报告，保留原文件；仅显式迁移时绑定 --legacy-pdf-sha256')
