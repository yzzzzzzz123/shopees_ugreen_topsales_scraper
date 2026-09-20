"""旧采集 CLI 的迁移边界；默认入口不能将历史表或浏览器复制路线静默回退。"""

import io
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills/shopee-ugreen-topsales/scripts"))
import run_scrape as runner


class KnownRunnerTests(unittest.TestCase):
    def test_retired_options_fail_with_actionable_migration_before_any_runtime(self):
        for option in sorted(runner.LEGACY_OPTIONS):
            with self.subTest(option=option), patch.object(runner, "_bound_project_root") as bind, redirect_stdout(io.StringIO()) as out, redirect_stderr(io.StringIO()) as err:
                with self.assertRaises(SystemExit) as raised:
                    runner.main(["--project-root", "/fixture", option])
            self.assertEqual(raised.exception.code, 2)
            bind.assert_not_called()
            self.assertEqual(out.getvalue(), "")
            self.assertIn("旧参数已迁移", err.getvalue())
            self.assertIn("--plan", err.getvalue())
            self.assertIn("skills/shopee-ugreen-topsales/assets/run_prompt_template.md", err.getvalue())

    def test_equals_syntax_cannot_bypass_retired_option_guard(self):
        with patch.object(runner, "_bound_project_root") as bind, redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                runner.main(["--reference-workbook=/old.xlsx"])
        bind.assert_not_called()

    def test_explicit_old_scope_confirmation_does_not_reenable_legacy_collection(self):
        with tempfile.TemporaryDirectory() as directory:
            reference = Path(directory) / "previous.xlsx"
            original = b"historical values must remain untouched"
            reference.write_bytes(original)
            with patch.object(runner, "_bound_project_root") as bind, redirect_stdout(io.StringIO()) as out, redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit):
                    runner.main(["--refresh-known-products", "--confirm-no-new-products", "--reference-workbook", str(reference)])
            self.assertEqual(reference.read_bytes(), original)
            self.assertEqual(list(Path(directory).iterdir()), [reference])
            self.assertEqual(out.getvalue(), "")
            bind.assert_not_called()

    def test_removed_browser_options_are_not_advertised_as_current_commands(self):
        help_text = runner._parser().format_help()
        self.assertIn("--publish-stdin", help_text)
        self.assertIn("--plan", help_text)
        self.assertNotIn("--refresh-known-products", help_text)
        self.assertNotIn("--browser-profile", help_text)


if __name__ == "__main__":
    unittest.main()
