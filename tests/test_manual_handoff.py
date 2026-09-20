"""人工交还控制协议：离线测试，不启动浏览器或读取真实 profile。"""

import asyncio
import io
import json
import sys
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills/shopee-ugreen-topsales/scripts"))
import scraper
import run_scrape as runner
from test_scraper import FIXTURE_VERSION, US_REGION, fingerprint


def child_with_events(events):
    stdout, stderr = asyncio.StreamReader(limit=64 * 1024 * 1024), asyncio.StreamReader()
    for event in events:
        stdout.feed_data((json.dumps(event) + "\n").encode())
    stderr.feed_eof()
    ended = asyncio.Event()
    commands = []

    def write(data):
        value = json.loads(data)
        commands.append(value)
        if value.get("command") == "accept":
            ended.set()

    async def wait():
        await ended.wait()
        return 0

    child = SimpleNamespace(stdin=SimpleNamespace(write=write, drain=AsyncMock(), close=MagicMock()),
                            stdout=stdout, stderr=stderr, wait=wait)
    return child, commands


class ManualBridgeTests(unittest.IsolatedAsyncioTestCase):
    async def test_valid_first_snapshot_continues_without_human_prompt(self):
        child, commands = child_with_events([{"event": "manual_snapshot", "snapshot": {}}])
        with patch.object(scraper, "_wait_for_manual_resume", new_callable=AsyncMock) as resume, \
                patch.object(scraper, "_validate_list_snapshot", return_value={}):
            await scraper._communicate_manual_capture(child, {}, 0, None, 1, None, fingerprint())
        resume.assert_not_awaited()
        self.assertEqual([c.get("command") for c in commands], [None, "accept"])

    async def test_real_parser_accepts_valid_list_with_internal_html_comments(self):
        from test_list_html import document, card, URL
        from test_node_bridge import snapshot
        value = snapshot()
        value.update(html=document(''.join(card(str(i)) for i in range(100, 130)),
                                   body='<!-- React marker -->'), final_url=URL)
        child, commands = child_with_events([
            {"event": "manual_handoff_ready"}, {"event": "manual_snapshot", "snapshot": value},
        ])
        with patch.object(scraper, "_wait_for_manual_resume", new_callable=AsyncMock):
            result = await scraper._communicate_manual_capture(child, {}, 0, None, 1, None, fingerprint())
        self.assertEqual(result, value)
        self.assertEqual(commands[-1], {"command": "accept"})

    async def test_snapshot_read_error_returns_to_manual_hold_without_closing(self):
        child, commands = child_with_events([
            {"event": "manual_handoff_ready"},
            {"event": "manual_snapshot_error", "error_kind": "runtime", "stage": "content"},
            {"event": "manual_handoff_ready"}, {"event": "manual_snapshot", "snapshot": {}},
        ])
        with patch.object(scraper, "_wait_for_manual_resume", new_callable=AsyncMock) as resume, \
                patch.object(scraper, "_validate_list_snapshot", return_value={}):
            await scraper._communicate_manual_capture(child, {}, 0, None, 1, None, fingerprint())
        self.assertEqual(resume.await_count, 2)
        self.assertEqual([c.get("command") for c in commands], [None, "resume", "resume", "accept"])

    async def test_parser_internal_error_keeps_window_for_recovery(self):
        child, commands = child_with_events([
            {"event": "manual_handoff_ready"}, {"event": "manual_snapshot", "snapshot": {}},
            {"event": "manual_handoff_ready"}, {"event": "manual_snapshot", "snapshot": {}},
        ])
        with patch.object(scraper, "_wait_for_manual_resume", new_callable=AsyncMock), \
                patch.object(scraper, "_validate_list_snapshot", side_effect=[AttributeError("private"), {}]):
            await scraper._communicate_manual_capture(child, {}, 0, None, 1, None, fingerprint())
        self.assertEqual([c.get("command") for c in commands], [None, "resume", "hold", "resume", "accept"])

    async def test_rejected_snapshot_holds_same_window_then_accepts_only_validated_snapshot(self):
        invalid, valid = {"html": "private-invalid"}, {"html": "private-valid"}
        child, commands = child_with_events([
            {"event": "manual_handoff_ready"}, {"event": "manual_snapshot", "snapshot": invalid},
            {"event": "manual_handoff_ready"}, {"event": "manual_snapshot", "snapshot": valid},
        ])
        messages = []
        with patch.object(scraper, "_wait_for_manual_resume", new_callable=AsyncMock) as resume, \
                patch.object(scraper, "_validate_list_snapshot", side_effect=[scraper.ScrapeError("blocked"), {}]) as validate:
            result = await scraper._communicate_manual_capture(child, {"url": "fixture"}, 0, None, 1, messages.append, fingerprint())
        self.assertEqual(result, valid)
        self.assertEqual(resume.await_count, 2)
        self.assertEqual(validate.call_count, 2)
        self.assertEqual([c.get("command") for c in commands], [None, "resume", "hold", "resume", "accept"])
        self.assertNotIn("private-", "".join(messages))

    async def test_human_wait_is_not_subject_to_capture_timeout(self):
        child, commands = child_with_events([
            {"event": "manual_handoff_ready"}, {"event": "manual_snapshot", "snapshot": {}},
        ])
        permission = asyncio.Event()
        async def resume(_):
            await permission.wait()
        with patch.object(scraper, "_wait_for_manual_resume", new=resume), \
                patch.object(scraper, "_validate_list_snapshot", return_value={}):
            task = asyncio.create_task(scraper._communicate_manual_capture(child, {}, 0, None, 0.01, None, fingerprint()))
            await asyncio.sleep(0.04)
            self.assertFalse(task.done())
            self.assertEqual(commands, [{}])
            permission.set()
            await task

    async def test_manual_failure_never_runs_automatic_three_attempt_restart(self):
        config = scraper.BrowserConfig(browser_profile="windows-intel", chrome_version=FIXTURE_VERSION, region=US_REGION, manual_list_handoff=True)
        with patch.object(scraper, "_capture_list_page_attempt", new=AsyncMock(side_effect=scraper.ScrapeError("cancelled"))) as capture, \
                patch.object(scraper.asyncio, "sleep", new_callable=AsyncMock) as sleep:
            with self.assertRaises(scraper.ScrapeError):
                await scraper._capture_list_page_with_profile(Path("/fixture"), 0, config, None)
        capture.assert_awaited_once()
        sleep.assert_not_awaited()


class ManualCliTests(unittest.TestCase):
    def test_cli_no_longer_selects_or_injects_browser_profiles(self):
        with patch.object(runner, "_bound_project_root") as bind, redirect_stderr(io.StringIO()) as errors:
            with self.assertRaises(SystemExit):
                runner.main(["--browser-profile", "auto"])
        bind.assert_not_called()
        self.assertIn("当前已有浏览器工具", errors.getvalue())

    def test_old_manual_cli_is_replaced_by_host_agent_handoff(self):
        for option in ("--manual-access", "--manual-list-handoff"):
            with self.subTest(option=option), patch.object(runner, "_bound_project_root") as bind, redirect_stderr(io.StringIO()) as errors:
                with self.assertRaises(SystemExit):
                    runner.main([option])
            bind.assert_not_called()
            self.assertIn("skills/shopee-ugreen-topsales/assets/run_prompt_template.md", errors.getvalue())


if __name__ == "__main__":
    unittest.main()
