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

from pacing import PACING_SPEED_MULTIPLIER, paced_wait_seconds


SKILL_RELATIVE = Path("skills/shopee-ugreen-topsales")
CONTRACT_DOCUMENTS = (
    "SKILL.md", "assets/run_prompt_template.md", "references/excel-output.md",
    "references/worktree.md", "references/capture-protocol.md", "references/daily-analysis.md",
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
    modes.add_argument("--resume-checkpoint", action="store_true", help="只读校验本轮进度表并报告可恢复详情/待办；不操作浏览器")
    modes.add_argument("--validate", action="store_true", help="独立只读验收明确指定的日期结果")
    modes.add_argument("--analyze", action="store_true", help="读取完整正式快照及历史，生成每日 PDF 分析报告")
    modes.add_argument("--archive", action="store_true", help="验收 Excel 和 PDF 后成对提交到日期分支，不推送远程")
    modes.add_argument("--check-contract", action="store_true", help="只读检查 Skill 内文档和 Excel 内容规范")
    parser.add_argument("--project-root", type=Path, help="当前 Skill 所属主项目根目录")
    parser.add_argument("--worktree", type=Path, help="--publish-stdin/--checkpoint-stdin/--validate 的明确日期 worktree")
    parser.add_argument("--date", help="仅 --prepare 可用，YYYY-MM-DD，必须为上海本日")
    parser.add_argument("--legacy-checkpoint-sha256", help="仅恢复旧版无内嵌状态的进度表时，绑定已审核且获准迁移的文件 SHA-256")
    parser.add_argument("--legacy-pdf-sha256", help="仅 --analyze 显式迁移一次性旧 PDF 时，绑定该文件 SHA-256")
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
        "analysis_output": str(worktree / "result/ugreen_topsales_analysis.pdf"),
        "history_storage": "date_branch_git_commits",
        "archive_mode": "--archive",
        "store_url": "https://shopee.ph/ugreen.ph?page=0&sortBy=sales&tab=0",
        "shop_id": "64922227",
        "currency": "PHP",
        "pacing_speed_multiplier": PACING_SPEED_MULTIPLIER,
        "minimum_interval_seconds": paced_wait_seconds(2),
        "maximum_interval_seconds": paced_wait_seconds(3),
        "randomized_navigation_interval": True,
        "batch_size": 50,
        "batch_cooldown_seconds": {"minimum": 0, "maximum": 0},
        "checkpoint_every_details": 50,
        "checkpoint_output": str(worktree / "result/ugreen_topsales_progress.xlsx"),
        "flush_checkpoint_on_stop": True,
        "durable_checkpoint_in_workbook": True,
        "resume_mode": "--resume-checkpoint",
        "challenge_action": "detach_then_checkpoint_wait_for_user",
        "ordinary_error_action": "recover_automatically_without_user_confirmation",
        "required_steps": [
            "读取 Skill 内任务书、内容规范及现场数据协议，冻结上海启动日；规范只读且不是业务种子。",
            "新一轮按 --prepare 自动提交并准备本日 worktree；续跑先恢复原日期进度，不重新 prepare 或重抓已完成详情。",
            "宿主 Agent 读取原 Chrome 目标页，确认 PH UGREEN 与 Top Sales；Playwright 每轮只建立一次长连接，检查、采集和保存复用同一连接与原 page，不频繁重连或重复触发授权。",
            "页面后台或失焦不暂停、不因此断开；普通读页/输入超时和解析失败由宿主自动恢复，不要求用户确认，不抢回焦点。",
            "A 路线默认完整 DOM 直读，不发送鼠标移动或滚轮；导航前检查当前页，按真实 URL 导航后随机驻留，读取完整 DOM 并核验后离线解析。",
            "人为等待统一按原值除以 2.5；导航间隔 0.8～1.2 秒、驻留 0.8～1.6 秒，普通重试退避同步缩短；不缩短操作超时上限，不跳过完整性或验证码检查。",
            "单路以每次随机 0.8～1.2 秒导航间隔读取本轮全部列表页；列表页和卡片不计入详情批次。",
            "逐个访问本轮每个唯一商品详情，核对身份、完整 model/SKU 和图库；缺字段不编造。",
            "详情阶段每完成 50 个商品累计保存进度 Excel，保存成功后继续，不额外冷却；停止和结束时保存不足 50 件的尾批。",
            "只有现场验证码/人工验证才立即断开、保存并交用户；普通超时自动恢复续跑，不把工具时限当验证码，不绕过登录/访问限制。",
            "将完整现场数据按 references/capture-protocol.md 通过 stdin JSON 交给 --publish-stdin；不落盘原始数据。",
            "执行 --analyze；分析器先独立重开验收完整 Excel，再读取合格历史，生成同目录 PDF。缺历史不伪造日环比或趋势。",
            "独立执行 --validate，核对四表和 PDF 与源表一致，再 --archive 将两份正式产物成对提交到日期分支；不提交进度表，不推送。同日替换前先归档上一对完整产物。",
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
    if args.publish_stdin or args.checkpoint_stdin or args.validate or args.resume_checkpoint or args.analyze or args.archive:
        if args.project_root is None or args.worktree is None:
            parser.error("--publish-stdin/--checkpoint-stdin/--validate/--resume-checkpoint/--analyze/--archive 必须明确指定 --project-root 与 --worktree")
    elif args.worktree is not None:
        parser.error("--worktree 仅用于 --publish-stdin、--checkpoint-stdin、--validate、--resume-checkpoint、--analyze 或 --archive")
    if args.legacy_pdf_sha256 is not None and not args.analyze:
        parser.error("--legacy-pdf-sha256 仅用于 --analyze")
    if args.legacy_checkpoint_sha256 is not None and not args.resume_checkpoint:
        parser.error("--legacy-checkpoint-sha256 仅用于 --resume-checkpoint")
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
        elif args.resume_checkpoint:
            from checkpoint_resume import load_checkpoint

            restored = load_checkpoint(root, args.worktree, legacy_sha256=args.legacy_checkpoint_sha256)
            receipt = {key: restored[key] for key in ("path", "sha256", "counts", "saved_count", "next_checkpoint_at", "origin")}
            receipt.update(status="checkpoint_restored", started_at=restored["payload"]["started_at"],
                           saved_at=restored["payload"]["captured_at"], browser_resumed=False)
        elif args.analyze:
            from analysis_report import write_report

            receipt = (write_report(root, args.worktree, legacy_pdf_sha256=args.legacy_pdf_sha256)
                       if args.legacy_pdf_sha256 else write_report(root, args.worktree))
        elif args.archive:
            from snapshot_history import archive_result
            receipt = archive_result(root, args.worktree)
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
