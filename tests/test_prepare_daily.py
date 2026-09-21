"""在临时 Git 仓库验证日期准备、自动提交和已有改动保留，不访问浏览器。"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPTS = Path(__file__).resolve().parents[1] / "skills/shopee-ugreen-topsales/scripts"
sys.path.insert(0, str(SCRIPTS))
import prepare_daily_worktree as prepare  # noqa: E402


class PrepareDailyTests(unittest.TestCase):
    def test_reused_worktree_reports_its_own_result_without_writing_workbooks(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            daily = root / "worktrees/20260917_ugreen_topsales"
            script = Path("skills/shopee-ugreen-topsales/scripts/run_scrape.py")
            for path in (root / ".venv/bin/python", root / script, daily / script):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.touch()
            legacy = root / "result/ugreen_topsales.xlsx"
            legacy.parent.mkdir()
            legacy.write_bytes(b"legacy main workbook")
            previous = root / "worktrees/20260916_ugreen_topsales/result/ugreen_topsales.xlsx"
            previous.parent.mkdir(parents=True)
            previous.write_bytes(b"previous daily workbook")

            def git(where, *args, **kwargs):
                self.assertIn(where, (root, daily))
                self.assertEqual(args, ("rev-parse", "HEAD"))
                return subprocess.CompletedProcess(args, 0, stdout="reviewed-head\n", stderr="")

            registration = [{"worktree": str(daily), "branch": "refs/heads/daily/20260917-ugreen-topsales"}]
            with patch.object(prepare, "_clean", return_value=True), patch.object(prepare, "_parse_worktrees", return_value=registration), patch.object(prepare, "_git", side_effect=git) as git_read:
                payload = prepare._prepare_locked(root, "2026-09-17")

            self.assertEqual(payload["status"], "reused")
            self.assertFalse(payload["created"])
            self.assertEqual(payload["project_root"], str(root))
            self.assertEqual(payload["worktree"], str(daily))
            self.assertEqual(payload["python"], str(root / ".venv/bin/python"))
            self.assertEqual(payload["runner"], str(daily / script))
            self.assertEqual(payload["output"], str(daily / "result/ugreen_topsales.xlsx"))
            self.assertEqual(git_read.call_count, 2)
            self.assertFalse((daily / "result").exists())
            self.assertEqual(legacy.read_bytes(), b"legacy main workbook")
            self.assertEqual(previous.read_bytes(), b"previous daily workbook")


class AutoCommitPrepareTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix="ugreen-prepare-git-")
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name).resolve()
        self.daily = self.root / "worktrees/20260921_ugreen_topsales"
        self.script = Path("skills/shopee-ugreen-topsales/scripts/run_scrape.py")
        for path in (self.root / ".venv/bin/python", self.root / self.script):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("initial\n", encoding="utf-8")
        (self.root / ".gitignore").write_text("/worktrees/\n/result/\n/.venv/\n", encoding="utf-8")
        self.git(self.root, "init", "-b", "main")
        self.git(self.root, "config", "user.name", "Temporary Fixture")
        self.git(self.root, "config", "user.email", "fixture@example.invalid")
        self.git(self.root, "add", ".")
        self.git(self.root, "commit", "-m", "initial")

    def git(self, root, *args):
        return prepare._git(root, *args).stdout.strip()

    def run_prepare(self):
        return prepare._prepare_locked(self.root, "2026-09-21")

    def test_dirty_main_is_committed_and_existing_daily_is_fast_forwarded(self):
        self.assertTrue(self.run_prepare()["created"])
        (self.root / self.script).write_text("updated\n", encoding="utf-8")
        (self.root / "new-source.txt").write_text("new\n", encoding="utf-8")
        receipt = self.run_prepare()
        self.assertTrue(receipt["source_commit"])
        self.assertTrue(receipt["synchronized"])
        self.assertEqual(receipt["source_head"], receipt["worktree_head"])
        self.assertEqual((self.daily / self.script).read_text(), "updated\n")
        self.assertEqual((self.daily / "new-source.txt").read_text(), "new\n")
        head = receipt["worktree_head"]
        reused = self.run_prepare()
        self.assertIsNone(reused["source_commit"])
        self.assertIsNone(reused["daily_commit"])
        self.assertFalse(reused["synchronized"])
        self.assertEqual(reused["worktree_head"], head)

    def test_daily_changes_and_ignored_result_survive_divergent_merge(self):
        self.run_prepare()
        (self.root / self.script).write_text("updated\n", encoding="utf-8")
        note = self.daily / "daily-note.txt"
        note.write_text("preserve me\n", encoding="utf-8")
        output = self.daily / "result/ugreen_topsales_progress.xlsx"
        output.parent.mkdir()
        output.write_bytes(b"existing result")
        receipt = self.run_prepare()
        self.assertTrue(receipt["source_commit"])
        self.assertTrue(receipt["daily_commit"])
        self.assertNotEqual(receipt["source_head"], receipt["worktree_head"])
        self.assertEqual((self.daily / self.script).read_text(), "updated\n")
        self.assertEqual(note.read_text(), "preserve me\n")
        self.assertEqual(output.read_bytes(), b"existing result")
        self.assertEqual(self.git(self.daily, "ls-files", "result"), "")
        self.assertEqual(self.git(self.root, "status", "--porcelain"), "")
        self.assertEqual(self.git(self.daily, "status", "--porcelain"), "")

    def test_existing_unchecked_out_old_daily_branch_is_updated(self):
        self.git(self.root, "branch", "daily/20260921-ugreen-topsales")
        (self.root / self.script).write_text("updated\n", encoding="utf-8")
        receipt = self.run_prepare()
        self.assertTrue(receipt["created"])
        self.assertTrue(receipt["synchronized"])
        self.assertEqual((self.daily / self.script).read_text(), "updated\n")

    def test_actual_merge_conflict_is_preserved_and_not_committed_on_retry(self):
        self.run_prepare()
        (self.root / self.script).write_text("main change\n", encoding="utf-8")
        (self.daily / self.script).write_text("daily change\n", encoding="utf-8")
        with self.assertRaisesRegex(prepare.WorktreeError, "merge"):
            self.run_prepare()
        head = self.git(self.daily, "rev-parse", "HEAD")
        content = (self.daily / self.script).read_text()
        self.assertIn("main change", content)
        self.assertIn("daily change", content)
        with self.assertRaisesRegex(prepare.WorktreeError, "合并冲突"):
            self.run_prepare()
        self.assertEqual(self.git(self.daily, "rev-parse", "HEAD"), head)
        self.assertEqual((self.daily / self.script).read_text(), content)


if __name__ == "__main__":
    unittest.main()
