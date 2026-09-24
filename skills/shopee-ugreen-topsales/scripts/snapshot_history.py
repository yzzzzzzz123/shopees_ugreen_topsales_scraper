"""把验收后的 Excel / PDF 成对保存在日期分支，Git 提交就是历史索引。"""
from __future__ import annotations

from datetime import datetime
import hashlib
from pathlib import Path
import re
import subprocess
import tempfile

from prepare_daily_worktree import WorktreeError, _git

WORKBOOK = 'result/ugreen_topsales.xlsx'
REPORT = 'result/ugreen_topsales_analysis.pdf'


def read_blob(daily: Path, revision: str, path: str = WORKBOOK) -> bytes:
    if not re.fullmatch(r'[0-9a-f]{40,64}',revision) or path not in (WORKBOOK,REPORT):
        raise ValueError('历史 Git 引用或文件名无效')
    process=subprocess.run(['git','show',f'{revision}:{path}'],cwd=daily,capture_output=True)
    if process.returncode:
        raise WorktreeError('无法读取历史快照 Git 对象：'+process.stderr.decode('utf-8',errors='replace'))
    return process.stdout


def revisions(daily: Path) -> list[str]:
    return _git(daily,'log','--format=%H','--',WORKBOOK).stdout.splitlines()


def latest_snapshot(root: Path, daily: Path, cutoff: str, excluded: list[str] | None = None):
    """只读候选历史；选择完成时间不晚于当前报告的最新版本，单日只选一份。"""
    from analysis_report import load_snapshot, _load_snapshot_file
    from validate_result import _target_workbook
    target=_target_workbook(root,daily)
    candidates=[];errors=[];seen=set()
    if target.is_file():
        try:
            snapshot=load_snapshot(root,daily)
            if snapshot.captured_at<=cutoff:candidates.append(snapshot)
            seen.add(snapshot.sha256)
        except Exception as exc:errors.append(str(exc))
    for revision in revisions(daily):
        try:
            content=read_blob(daily,revision)
            sha=hashlib.sha256(content).hexdigest()
            if sha in seen:continue
            seen.add(sha)
            # validate_excel 接受路径；仅短暂展开已提交的工作簿，不覆盖工作区。
            with tempfile.TemporaryDirectory(prefix='ugreen-history-') as folder:
                scratch=Path(folder)/'snapshot.xlsx';scratch.write_bytes(content)
                snapshot=_load_snapshot_file(scratch,daily)
            snapshot.path=target;snapshot.revision=revision
            if snapshot.captured_at<=cutoff:candidates.append(snapshot)
        except Exception as exc:errors.append(f'{revision[:12]}：{exc}')
    if not candidates:
        if errors:raise ValueError('；'.join(errors))
        if seen:raise ValueError('历史快照完成时间晚于当前快照，不用于回看分析')
        return None
    if excluded is not None:
        excluded.extend(errors)
    return max(candidates,key=lambda s:(s.captured_at,s.revision is None))


def _archive_locked(root: Path, daily: Path) -> dict:
    from analysis_report import validate_report, load_snapshot, digest
    from publish_result import _check_destination
    from validate_result import _target_workbook
    target=_target_workbook(root,daily)
    _check_destination(target)
    branch=f'daily/{daily.name[:8]}-ugreen-topsales'
    if _git(daily,'symbolic-ref','--quiet','--short','HEAD').stdout.strip()!=branch:
        raise ValueError('历史快照只能提交到对应日期分支')
    if _git(daily,'ls-files','--unmerged').stdout:
        raise ValueError('日期分支存在合并冲突，保留现场后先解决冲突')
    receipt=validate_report(root,daily)
    snapshot=load_snapshot(root,daily)
    hashes={WORKBOOK:snapshot.sha256,REPORT:receipt['sha256']}
    # 仅暂存两份正式文件，不混入进度表、旧 Markdown 或任何已有其他改动。
    _git(daily,'add','-f','--',WORKBOOK,REPORT)
    changed=_git(daily,'diff','--cached','--quiet','--',WORKBOOK,REPORT,check=False)
    if changed.returncode not in (0,1):raise WorktreeError('无法比较待归档快照')
    if changed.returncode:
        _git(daily,'log','-5','--format=%s')
        _git(daily,'diff','--cached','--stat','--',WORKBOOK,REPORT)
        stamp=datetime.strptime(snapshot.captured_at,'%Y/%m/%d %H:%M:%S').strftime('%m-%d %H:%M:%S')
        signature=hashlib.sha256((hashes[WORKBOOK]+hashes[REPORT]).encode()).hexdigest()[:10]
        message=f'保存 UGREEN {snapshot.day} 完整快照与 PDF 分析（采集 {stamp}，{signature}）'
        _git(daily,'commit','--only','-m',message,'--',WORKBOOK,REPORT)
    revision=_git(daily,'rev-parse','HEAD').stdout.strip()
    for relative,expected in hashes.items():
        if hashlib.sha256(read_blob(daily,revision,relative)).hexdigest()!=expected or digest(daily/relative)!=expected:
            raise ValueError('Git 归档回读与正式文件不一致，请保留现场核查')
    return dict(archive_status='通过',branch=branch,commit=revision,created=bool(changed.returncode),
                report_date=snapshot.day.isoformat(),captured_at=snapshot.captured_at,files=hashes)


def archive_result(root: Path, daily: Path) -> dict:
    from publish_result import _exclusive_publish
    from validate_result import _target_workbook
    _target_workbook(root,daily)
    with _exclusive_publish(root.resolve()):
        return _archive_locked(root.resolve(),daily.resolve())


def preserve_previous_result(root: Path, daily: Path):
    """同日替换前保全上一对完整产物；调用方已持有发布锁。"""
    if (daily/REPORT).exists():
        return _archive_locked(root,daily)
    return None
