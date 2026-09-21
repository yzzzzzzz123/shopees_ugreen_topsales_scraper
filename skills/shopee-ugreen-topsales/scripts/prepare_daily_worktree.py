#!/usr/bin/env python3
"""为 UGREEN 每日任务创建或安全复用按日期命名的 Git worktree。"""

from __future__ import annotations

import argparse
import fcntl
import json
import subprocess
import sys
from contextlib import contextmanager
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo


class WorktreeError(RuntimeError):
    pass


@contextmanager
def _exclusive_lock(path: Path):
    """另一个进程正在准备每日 worktree 时立即失败。"""

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+", encoding="utf-8") as handle:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise WorktreeError(
                "已有另一个每日 worktree 准备任务正在运行"
            ) from exc
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _git(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        ["git", *args],
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise WorktreeError(f"git {' '.join(args)} 执行失败：{detail}")
    return completed


def _project_root(start: Path) -> Path:
    common = _git(
        start,
        "rev-parse",
        "--path-format=absolute",
        "--git-common-dir",
    ).stdout.strip()
    common_dir = Path(common).resolve()
    root = common_dir.parent
    if common_dir.name != ".git" or not (root / ".git").exists():
        raise WorktreeError(f"不支持的 Git 目录布局：{common_dir}")
    return root


def _parse_worktrees(root: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    current: dict[str, str] = {}
    for line in _git(root, "worktree", "list", "--porcelain").stdout.splitlines():
        if not line:
            if current:
                rows.append(current)
                current = {}
            continue
        key, _, value = line.partition(" ")
        current[key] = value
    if current:
        rows.append(current)
    return rows


def _clean(root: Path) -> bool:
    return not _git(
        root,
        "status",
        "--porcelain",
        "--untracked-files=all",
    ).stdout.strip()


def _auto_commit(root: Path, message: str) -> str | None:
    """保存本项目非 ignored 的现有改动；无改动时不生成空提交。"""
    if _clean(root):
        return None
    if _git(root, "ls-files", "--unmerged").stdout:
        raise WorktreeError(f"存在尚未解决的实际合并冲突，保留改动：{root}")
    _git(root, "add", "-A", "--", ".")
    _git(root, "commit", "-m", message)
    return _git(root, "rev-parse", "HEAD").stdout.strip()


def _run_date(value: str | None) -> date:
    if value is None:
        return datetime.now(ZoneInfo("Asia/Shanghai")).date()
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise WorktreeError("--date 必须使用 YYYY-MM-DD 格式") from exc
    if parsed.isoformat() != value:
        raise WorktreeError("--date 必须使用补零后的 YYYY-MM-DD 格式")
    return parsed


def _prepare_locked(root: Path, value: str | None) -> dict[str, object]:
    python = root / ".venv/bin/python"
    source_runner = root / "skills/shopee-ugreen-topsales/scripts/run_scrape.py"
    if not python.is_file():
        raise WorktreeError(f"主项目 Python 环境不存在：{python}")
    if not source_runner.is_file():
        raise WorktreeError(f"主项目 runner 不存在：{source_runner}")

    run_date = _run_date(value)
    compact = run_date.strftime("%Y%m%d")
    branch = f"daily/{compact}-ugreen-topsales"
    worktree_root = root / "worktrees"
    worktree = worktree_root / f"{compact}_ugreen_topsales"
    if worktree_root.is_symlink():
        raise WorktreeError(f"worktrees 目录不能是符号链接：{worktree_root}")
    if worktree.is_symlink():
        raise WorktreeError(f"当日 worktree 路径不能是符号链接：{worktree}")
    expected_branch = f"refs/heads/{branch}"
    registrations = _parse_worktrees(root)

    registered_here = next(
        (
            row
            for row in registrations
            if Path(row.get("worktree", "")).resolve() == worktree.resolve()
        ),
        None,
    )
    branch_elsewhere = next(
        (row for row in registrations if row.get("branch") == expected_branch),
        None,
    )

    if registered_here:
        if registered_here.get("branch") != expected_branch:
            raise WorktreeError(
                f"当日路径注册到 {registered_here.get('branch')!r}，"
                f"但预期为 {expected_branch!r}"
            )
    else:
        if worktree.exists():
            raise WorktreeError(
                f"当日路径已存在，但不是本仓库注册的 Git worktree：{worktree}"
            )
        if branch_elsewhere:
            raise WorktreeError(
                f"当日分支已在其他位置检出：{branch_elsewhere.get('worktree')}"
            )

    source_commit = _auto_commit(root, f"chore: save UGREEN source before {compact} run")
    primary_head = _git(root, "rev-parse", "HEAD").stdout.strip()
    created = registered_here is None
    if created:
        worktree_root.mkdir(parents=True, exist_ok=True)
        branch_exists = (
            _git(root, "show-ref", "--verify", "--quiet", expected_branch, check=False).returncode
            == 0
        )
        if branch_exists:
            _git(root, "worktree", "add", str(worktree), branch)
        else:
            _git(root, "worktree", "add", "-b", branch, str(worktree), "HEAD")

    daily_commit = _auto_commit(worktree, f"chore: save UGREEN daily changes for {compact}")
    daily_head = _git(worktree, "rev-parse", "HEAD").stdout.strip()
    synchronized = daily_head != primary_head
    if synchronized:
        # 正常快进或保留双方提交的合并；不 reset、不丢弃日期工作区改动。
        _git(worktree, "merge", "--no-edit", primary_head)
        daily_head = _git(worktree, "rev-parse", "HEAD").stdout.strip()

    runner = worktree / "skills/shopee-ugreen-topsales/scripts/run_scrape.py"
    if not runner.is_file():
        raise WorktreeError(f"当日 runner 不存在：{runner}")

    return {
        "status": "created" if created else "reused",
        "date": run_date.isoformat(),
        "project_root": str(root),
        "worktree": str(worktree),
        "branch": branch,
        "created": created,
        "source_commit": source_commit,
        "daily_commit": daily_commit,
        "synchronized": synchronized,
        "source_head": primary_head,
        "worktree_head": daily_head,
        "python": str(python),
        "runner": str(runner),
        "output": str(worktree / "result/ugreen_topsales.xlsx"),
    }


def prepare(value: str | None) -> dict[str, object]:
    invocation_root = Path(__file__).resolve().parent
    root = _project_root(invocation_root)
    with _exclusive_lock(root / ".git/ugreen_daily.lock"):
        return _prepare_locked(root, value)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--date",
        help="Asia/Shanghai 运行日期，格式 YYYY-MM-DD；默认今天",
    )
    args = parser.parse_args()
    try:
        payload = prepare(args.date)
    except (OSError, WorktreeError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2
    print(json.dumps(payload, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
