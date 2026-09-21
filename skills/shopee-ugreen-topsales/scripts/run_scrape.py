#!/usr/bin/env python3
"""宿主 Agent 的全量任务交接入口；此命令不访问网页或启动浏览器。"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Sequence
from zoneinfo import ZoneInfo


SKILL_RELATIVE = Path("skills/shopee-ugreen-topsales")
CONTRACT_DOCUMENTS = (
    "SKILL.md", "assets/run_prompt_template.md", "references/excel-output.md",
    "references/worktree.md", "references/capture-protocol.md",
)
LEGACY_OPTIONS = frozenset({
    "--verify-access", "--manual-access", "--manual-list-handoff",
    "--historical-list-preflight", "--refresh-known-products",
    "--confirm-no-new-products", "--reference-workbook", "--headless",
    "--detail-shards", "--detail-workers", "--list-interval-seconds",
    "--detail-interval-seconds", "--browser-profile", "--chrome-executable",
})


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__, allow_abbrev=False,
        epilog="默认只返回任务计划，不表示已采集；现场浏览器步骤见 skills/shopee-ugreen-topsales/assets/run_prompt_template.md。",
    )
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--plan", action="store_true", help="只读输出全量任务交接计划（默认）")
    modes.add_argument("--prepare", action="store_true", help="自动提交改动并创建或更新上海本日 worktree")
    modes.add_argument("--publish-stdin", action="store_true", help="验收 stdin 现场 JSON 并原子发布四表")
    modes.add_argument("--checkpoint-stdin", action="store_true", help="保存本轮已采集数据为累计进度 Excel，不表示全量完成")
    modes.add_argument("--validate", action="store_true", help="独立只读验收明确指定的日期结果")
    modes.add_argument("--check-contract", action="store_true", help="只读检查 Skill 内文档和 Excel 内容规范")
    parser.add_argument("--project-root", type=Path, help="当前 Skill 所属主项目根目录")
    parser.add_argument("--worktree", type=Path, help="--publish-stdin/--checkpoint-stdin/--validate 的明确日期 worktree")
    parser.add_argument("--date", help="仅 --prepare 可用，YYYY-MM-DD，必须为上海本日")
    return parser


def _bound_project_root(value: Path | None) -> Path:
    from prepare_daily_worktree import _project_root

    expected = _project_root(Path(__file__).resolve().parent)
    if value is None:
        return expected
    if ".." in value.parts or value.expanduser().is_symlink():
        raise ValueError("--project-root 不能包含 .. 或指向符号链接")
    if value.expanduser().resolve() != expected:
        raise ValueError(f"--project-root 必须是当前 Skill 的主项目：{expected}")
    return expected


def _contract_files(root: Path) -> dict[str, str]:
    skill = root / SKILL_RELATIVE
    for directory in (root / "skills", skill, skill / "assets", skill / "references"):
        if directory.is_symlink() or not directory.is_dir():
            raise ValueError(f"规范目录不存在或为符号链接：{directory}")
    paths = {name: skill / name for name in (*CONTRACT_DOCUMENTS, "assets/ugreen_topsales.xlsx")}
    for path in paths.values():
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"规范文件不存在或不是安全常规文件：{path}")
    return {name: str(path) for name, path in paths.items()}


def _plan(root: Path, run_date: date) -> dict:
    contracts = _contract_files(root)
    compact = run_date.strftime("%Y%m%d")
    worktree = root / "worktrees" / f"{compact}_ugreen_topsales"
    return {
        "status": "awaiting_browser_collection",
        "mode": "full_store_top_sales",
        "project_root": str(root),
        "taskbook": contracts["assets/run_prompt_template.md"],
        "contract_documents": {name: contracts[name] for name in CONTRACT_DOCUMENTS},
        "excel_contract": contracts["assets/ugreen_topsales.xlsx"],
        "run_date": run_date.isoformat(),
        "timezone": "Asia/Shanghai",
        "branch": f"daily/{compact}-ugreen-topsales",
        "worktree": str(worktree),
        "expected_output": str(worktree / "result/ugreen_topsales.xlsx"),
        "store_url": "https://shopee.ph/ugreen.ph?page=0&sortBy=sales&tab=0",
        "shop_id": "64922227",
        "currency": "PHP",
        "minimum_interval_seconds": 2,
        "maximum_interval_seconds": 3,
        "randomized_navigation_interval": True,
        "batch_size": 50,
        "batch_cooldown_seconds": {"minimum": 180, "maximum": 300},
        "checkpoint_every_details": 50,
        "checkpoint_output": str(worktree / "result/ugreen_topsales_progress.xlsx"),
        "flush_checkpoint_on_stop": True,
        "challenge_action": "detach_then_checkpoint_wait_for_user",
        "required_steps": [
            "读取 Skill 内任务书、内容规范及现场数据协议，冻结上海启动日；规范只读且不是业务种子。",
            "按 --prepare 自动提交项目改动并创建或更新本日 worktree；不以脏状态或 HEAD 不同阻断采集和发布。",
            "宿主 Agent 读取原 Chrome 目标页，确认 PH UGREEN 与 Top Sales；Playwright 每轮只建立一次长连接，检查、采集、保存和冷却复用同一连接与原 page，不频繁重连或重复触发授权。",
            "页面后台或失焦不暂停、不因此断开；页面可正常读取且身份、完整性通过就继续，不抢回焦点。实际读页或输入失败、超时仍按异常处理。",
            "A 路线每页按 Skill 第 4 节调用 page_browse.py：正常页检查、分段滚轮与随机停留，最终 DOM 离线解析；滚动不保证免验证码。",
            "单路以每次随机 2～3 秒导航间隔读取本轮全部列表页；列表页和卡片不计入详情批次。",
            "逐个访问本轮每个唯一商品详情，核对身份、完整 model/SKU 和图库；缺字段不编造。",
            "详情阶段每完成 50 个商品累计保存进度 Excel，再随机冷却 3～5 分钟；停止和结束时保存不足 50 件的尾批。",
            "登录、验证码或访问挑战先立即断开自动化、保留原页，再保存已有数据；等待用户明确继续后才重新附着验收，不自动重连。",
            "将完整现场数据按 references/capture-protocol.md 通过 stdin JSON 交给 --publish-stdin；不落盘原始数据。",
            "独立执行 --validate，核对四表与抓取核验；全部通过后才交付日期 Excel。",
        ],
        "full_crawl_completed": False,
        "workbook_written": False,
    }


def _read_capture_payload() -> dict:
    def reject_constant(value: str):
        raise ValueError(f"stdin JSON 不允许非有限常量：{value}")

    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"stdin JSON 包含重复字段：{key}")
            result[key] = value
        return result

    payload = json.load(sys.stdin, parse_constant=reject_constant, object_pairs_hook=unique_object)
    if not isinstance(payload, dict):
        raise ValueError("stdin 必须是 references/capture-protocol.md 定义的现场 JSON 对象，不接受历史工作簿路径")
    return payload


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    raw = list(sys.argv[1:] if argv is None else argv)
    retired = sorted({arg.split("=", 1)[0] for arg in raw} & LEGACY_OPTIONS)
    if retired:
        parser.error(
            f"旧参数已迁移：{', '.join(retired)}。请用 --plan 读取 skills/shopee-ugreen-topsales/assets/run_prompt_template.md，"
            "由宿主 Agent 通过当前已有浏览器工具现场采集，再 --publish-stdin；"
            "不再从此入口启动浏览器、复制 profile 或以历史表作种子。"
        )
    args = parser.parse_args(raw)
    if args.publish_stdin or args.checkpoint_stdin or args.validate:
        if args.project_root is None or args.worktree is None:
            parser.error("--publish-stdin/--checkpoint-stdin/--validate 必须明确指定 --project-root 与 --worktree")
    elif args.worktree is not None:
        parser.error("--worktree 仅用于 --publish-stdin、--checkpoint-stdin 或 --validate")
    if args.date is not None and not args.prepare:
        parser.error("--date 仅用于 --prepare，且只允许上海本日")

    try:
        root = _bound_project_root(args.project_root)
        run_date = datetime.now(ZoneInfo("Asia/Shanghai")).date()
        if args.prepare:
            if args.date is not None:
                requested = date.fromisoformat(args.date)
                if args.date != requested.isoformat() or requested != run_date:
                    raise ValueError("--prepare 只允许上海本日，不创建或改动其他日期 worktree")
            from prepare_daily_worktree import prepare

            receipt = prepare(run_date.isoformat())
        elif args.publish_stdin:
            from publish_result import publish

            receipt = publish(_read_capture_payload(), root, args.worktree)
        elif args.checkpoint_stdin:
            from checkpoint_result import write_snapshot

            receipt = write_snapshot(_read_capture_payload(), root, args.worktree)
        elif args.validate:
            from validate_result import main as validate_main

            return validate_main(["--project-root", str(root), "--worktree", str(args.worktree)])
        elif args.check_contract:
            from publish_result import validate_template_contract

            documents = _contract_files(root)
            receipt = {
                "status": "contract_checked",
                "contract_documents": {name: documents[name] for name in CONTRACT_DOCUMENTS},
                "excel_contract": validate_template_contract(root),
                "full_crawl_completed": False,
                "workbook_written": False,
            }
        else:
            receipt = _plan(root, run_date)
        print(json.dumps(receipt, ensure_ascii=False, allow_nan=False))
        return 0
    except KeyboardInterrupt:
        print("已中止；未宣称采集或发布完成。", file=sys.stderr)
        return 130
    except Exception as exc:
        print(f"失败：{type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
