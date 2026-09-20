"""宿主 Agent 入口的离线交接测试；不访问网站、不改真实 Git/工作簿。"""

from __future__ import annotations

import builtins
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch


SCRIPTS = Path(__file__).resolve().parents[1] / "skills/shopee-ugreen-topsales/scripts"
sys.path.insert(0, str(SCRIPTS))
import run_scrape as runner


class RunnerTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.skill = self.root / runner.SKILL_RELATIVE
        for name in runner.CONTRACT_DOCUMENTS:
            document = self.skill / name
            document.parent.mkdir(parents=True, exist_ok=True)
            document.write_text("# Offline fixture", encoding="utf-8")
        (self.skill / "assets/ugreen_topsales.xlsx").write_bytes(b"schema placeholder; plan never parses business values")
        clock_patch = patch.object(runner, "datetime")
        self.clock = clock_patch.start()
        self.addCleanup(clock_patch.stop)
        self.clock.now.side_effect = lambda zone: datetime(2026, 9, 20, 12, tzinfo=zone)
        bind_patch = patch.object(runner, "_bound_project_root", return_value=self.root)
        self.bind = bind_patch.start()
        self.addCleanup(bind_patch.stop)
        self.daily = self.root / "worktrees/20260920_ugreen_topsales"

    def invoke(self, *options, stdin="", modules=None):
        out, err = io.StringIO(), io.StringIO()
        with patch.object(sys, "stdin", io.StringIO(stdin)), patch.dict(sys.modules, modules or {}), redirect_stdout(out), redirect_stderr(err):
            code = runner.main(list(options))
        return code, out.getvalue(), err.getvalue()

    def bound_options(self, mode):
        return (mode, "--project-root", str(self.root), "--worktree", str(self.daily))

    def test_default_is_read_only_full_store_plan_not_completed_crawl(self):
        before = {str(p.relative_to(self.root)): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        code, output, errors = self.invoke()
        plan = json.loads(output)
        self.assertEqual((code, errors), (0, ""))
        self.assertEqual(plan["status"], "awaiting_browser_collection")
        self.assertEqual(plan["mode"], "full_store_top_sales")
        self.assertEqual(plan["taskbook"], str(self.skill / "assets/run_prompt_template.md"))
        self.assertEqual(plan["excel_contract"], str(self.skill / "assets/ugreen_topsales.xlsx"))
        self.assertEqual(plan["expected_output"], str(self.daily / "result/ugreen_topsales.xlsx"))
        self.assertEqual(plan["run_date"], "2026-09-20")
        self.assertEqual(plan["branch"], "daily/20260920-ugreen-topsales")
        self.assertEqual(plan["shop_id"], "64922227")
        self.assertEqual(plan["minimum_interval_seconds"], 10)
        self.assertEqual(set(plan["contract_documents"]), set(runner.CONTRACT_DOCUMENTS))
        self.assertGreater(len(plan["required_steps"]), 1)
        self.assertIs(plan["full_crawl_completed"], False)
        self.assertIs(plan["workbook_written"], False)
        self.assertFalse(self.daily.exists())
        after = {str(p.relative_to(self.root)): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        self.assertEqual(after, before)
        self.clock.now.assert_called_once()
        self.assertEqual(self.clock.now.call_args.args[0].key, "Asia/Shanghai")

    def test_explicit_plan_and_default_match(self):
        self.assertEqual(self.invoke(), self.invoke("--plan", "--project-root", str(self.root)))

    def test_plan_does_not_import_any_browser_or_publication_module(self):
        imported = []
        real_import = builtins.__import__

        def record(name, *args, **kwargs):
            imported.append(name)
            if name in {"scraper", "browser_fingerprint", "playwright", "publish_result", "validate_result"}:
                raise AssertionError(f"unexpected import: {name}")
            return real_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=record):
            self.assertEqual(self.invoke("--plan")[0], 0)
        self.assertNotIn("scraper", imported)

    def test_plan_rejects_missing_contract_without_creating_it(self):
        (self.skill / "assets/run_prompt_template.md").unlink()
        code, output, errors = self.invoke()
        self.assertEqual((code, output), (1, ""))
        self.assertIn("run_prompt_template.md", errors)
        self.assertFalse((self.root / "worktrees").exists())

    def test_contract_symlink_is_rejected(self):
        original = self.skill / "assets/run_prompt_template.md"
        original.unlink()
        original.symlink_to(self.skill / "SKILL.md")
        self.assertEqual(self.invoke("--plan")[0], 1)

    def test_prepare_delegates_frozen_current_date_without_claiming_crawl(self):
        prepare = Mock(return_value={"status": "created", "worktree": str(self.daily)})
        code, output, _ = self.invoke("--prepare", "--date", "2026-09-20", modules={"prepare_daily_worktree": SimpleNamespace(prepare=prepare)})
        self.assertEqual(code, 0)
        prepare.assert_called_once_with("2026-09-20")
        self.assertEqual(json.loads(output)["status"], "created")
        self.assertFalse(self.daily.exists())

    def test_prepare_defaults_to_shanghai_today(self):
        prepare = Mock(return_value={"status": "reused"})
        self.assertEqual(self.invoke("--prepare", modules={"prepare_daily_worktree": SimpleNamespace(prepare=prepare)})[0], 0)
        prepare.assert_called_once_with("2026-09-20")

    def test_prepare_refuses_other_dates_and_invalid_dates_before_mutation(self):
        for supplied in ("2026-09-19", "2026-09-21", "20260920", "2026-9-20", "not-a-date"):
            prepare = Mock()
            with self.subTest(supplied=supplied):
                code, output, _ = self.invoke("--prepare", "--date", supplied, modules={"prepare_daily_worktree": SimpleNamespace(prepare=prepare)})
                self.assertEqual((code, output), (1, ""))
                prepare.assert_not_called()

    def test_prepare_dirty_state_failure_is_not_cleaned_or_retried(self):
        prepare = Mock(side_effect=ValueError("主项目存在未提交改动"))
        code, output, errors = self.invoke("--prepare", modules={"prepare_daily_worktree": SimpleNamespace(prepare=prepare)})
        self.assertEqual((code, output), (1, ""))
        self.assertIn("未提交改动", errors)
        prepare.assert_called_once()

    def test_publish_forwards_only_stdin_object_and_exact_output_identity(self):
        payload = {"schema_version": "1.0", "pages": [], "details": []}
        receipt = {"status": "published", "path": str(self.daily / "result/ugreen_topsales.xlsx")}
        publish = Mock(return_value=receipt)
        code, output, errors = self.invoke(*self.bound_options("--publish-stdin"), stdin=json.dumps(payload), modules={"publish_result": SimpleNamespace(publish=publish)})
        self.assertEqual((code, errors), (0, ""))
        publish.assert_called_once_with(payload, self.root, self.daily)
        self.assertEqual(json.loads(output), receipt)
        self.assertFalse(self.daily.exists())

    def test_publish_requires_strict_json_object_and_does_not_read_paths(self):
        for value in ("", "/old.xlsx", '"/old.xlsx"', "[]", "null", '{"x":NaN}', '{"x":Infinity}', '{"x":1,"x":2}', '{}{}'):
            publish = Mock()
            with self.subTest(value=value):
                code, output, _ = self.invoke(*self.bound_options("--publish-stdin"), stdin=value, modules={"publish_result": SimpleNamespace(publish=publish)})
                self.assertEqual((code, output), (1, ""))
                publish.assert_not_called()

    def test_publish_failure_has_no_success_receipt(self):
        publish = Mock(side_effect=ValueError("缺少本轮详情"))
        code, output, errors = self.invoke(*self.bound_options("--publish-stdin"), stdin="{}", modules={"publish_result": SimpleNamespace(publish=publish)})
        self.assertEqual((code, output), (1, ""))
        self.assertIn("缺少本轮详情", errors)

    def test_validate_delegates_explicit_paths_and_exit_code(self):
        validate = Mock(return_value=2)
        code, output, _ = self.invoke(*self.bound_options("--validate"), modules={"validate_result": SimpleNamespace(main=validate)})
        self.assertEqual((code, output), (2, ""))
        validate.assert_called_once_with(["--project-root", str(self.root), "--worktree", str(self.daily)])

    def test_check_contract_uses_shared_read_only_schema_validator(self):
        check = Mock(return_value={"path": str(self.skill / "assets/ugreen_topsales.xlsx"), "sha256": "fixture"})
        code, output, _ = self.invoke("--check-contract", modules={"publish_result": SimpleNamespace(validate_template_contract=check)})
        self.assertEqual(code, 0)
        check.assert_called_once_with(self.root)
        result = json.loads(output)
        self.assertEqual(result["status"], "contract_checked")
        self.assertIs(result["full_crawl_completed"], False)
        self.assertIs(result["workbook_written"], False)

    def test_check_contract_schema_mismatch_fails(self):
        check = Mock(side_effect=ValueError("表头不匹配"))
        code, output, errors = self.invoke("--check-contract", modules={"publish_result": SimpleNamespace(validate_template_contract=check)})
        self.assertEqual((code, output), (1, ""))
        self.assertIn("表头不匹配", errors)

    def test_argument_errors_precede_root_binding_or_actions(self):
        cases = (["--publish-stdin"], ["--validate"], ["--validate", "--worktree", str(self.daily)],
                 ["--publish-stdin", "--project-root", str(self.root)], ["--plan", "--prepare"],
                 ["--worktree", str(self.daily)], ["--date", "2026-09-20"], ["--pub"])
        for options in cases:
            self.bind.reset_mock()
            with self.subTest(options=options), redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as raised:
                runner.main(options)
            self.assertEqual(raised.exception.code, 2)
            self.bind.assert_not_called()

    def test_keyboard_interrupt_does_not_claim_completion(self):
        self.bind.side_effect = KeyboardInterrupt()
        code, output, errors = self.invoke()
        self.assertEqual((code, output), (130, ""))
        self.assertIn("未宣称", errors)


class ProjectBindingTests(unittest.TestCase):
    def test_explicit_other_root_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            with patch.dict(sys.modules, {"prepare_daily_worktree": SimpleNamespace(_project_root=Mock(return_value=root))}):
                self.assertEqual(runner._bound_project_root(None), root)
                self.assertEqual(runner._bound_project_root(root), root)
                with self.assertRaisesRegex(ValueError, "当前 Skill"):
                    runner._bound_project_root(root / "other")
                with self.assertRaisesRegex(ValueError, "不能包含"):
                    runner._bound_project_root(root / "child/..")


if __name__ == "__main__":
    unittest.main()
