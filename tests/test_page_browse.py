"""Behavioral checks for wheel browsing; live compatibility is tested separately."""
from __future__ import annotations

from pathlib import Path
import random
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'skills/shopee-ugreen-topsales/scripts'))
from page_browse import BrowserHandoff, BrowseInterrupted, DetachFailed, read_page_after_browsing

STORE = 'https://shopee.ph/ugreen.ph?page=0&sortBy=sales&tab=0'


class BrowserHandoffTests(unittest.TestCase):
    def test_detach_precedes_checkpoint_and_error_reporting(self):
        events = []
        gate = BrowserHandoff(lambda: events.append('detach'), on_handoff=lambda: events.append('save'))
        with self.assertRaises(ValueError):
            gate.run(Mock(side_effect=ValueError('challenge')))
        events.append('report')
        self.assertEqual(events, ['detach', 'save', 'report'])

    def test_failed_tail_save_still_leaves_control_released_and_locked(self):
        detach = Mock()
        gate = BrowserHandoff(detach, on_handoff=Mock(side_effect=OSError('disk full')))
        with self.assertRaisesRegex(RuntimeError, '连接已断开；尾批 Excel 保存失败'):
            gate.run(Mock(side_effect=ValueError('challenge')))
        detach.assert_called_once_with()
        self.assertTrue(gate.waiting_for_user)

    def test_tail_save_attempted_even_when_disconnect_cannot_be_confirmed(self):
        save = Mock()
        gate = BrowserHandoff(Mock(side_effect=OSError('detach')), on_handoff=save)
        with self.assertRaises(DetachFailed):
            gate.run(Mock(side_effect=ValueError('challenge')))
        save.assert_called_once_with()

    def test_success_keeps_connection_and_returns_result(self):
        detach = Mock()
        gate = BrowserHandoff(detach)
        for x in range(3):
            self.assertEqual(gate.run(lambda x, *, y: x + y, x, y=3), x + 3)
        self.assertFalse(gate.waiting_for_user)
        detach.assert_not_called()

    def test_failure_detaches_before_reporting_and_preserves_exception(self):
        events = []
        gate = BrowserHandoff(lambda: events.append('detach'))
        failure = BrowseInterrupted('challenge')

        def detect():
            events.append('detected')
            raise failure

        with self.assertRaises(BrowseInterrupted) as error:
            gate.run(detect)
        events.append('reported')
        self.assertIs(error.exception, failure)
        self.assertEqual(events, ['detected', 'detach', 'reported'])
        self.assertTrue(gate.waiting_for_user)

    def test_after_handoff_no_operation_or_detach_is_repeated(self):
        detach = Mock()
        gate = BrowserHandoff(detach)
        with self.assertRaises(ValueError):
            gate.run(Mock(side_effect=ValueError('challenge')))
        operation = Mock()
        with self.assertRaisesRegex(RuntimeError, '等待用户'):
            gate.run(operation)
        operation.assert_not_called()
        detach.assert_called_once_with()

    def test_nested_capture_guards_detach_only_once(self):
        detach = Mock()
        gate = BrowserHandoff(detach)
        with self.assertRaises(ValueError):
            gate.run(lambda: gate.run(Mock(side_effect=ValueError('challenge'))))
        detach.assert_called_once_with()

    def test_keyboard_interrupt_also_releases_control(self):
        detach = Mock()
        gate = BrowserHandoff(detach)
        with self.assertRaises(KeyboardInterrupt):
            gate.run(Mock(side_effect=KeyboardInterrupt()))
        detach.assert_called_once_with()
        self.assertTrue(gate.waiting_for_user)

    def test_detach_failure_is_not_reported_as_disconnected(self):
        detach = Mock(side_effect=OSError('transport failure'))
        gate = BrowserHandoff(detach)
        with self.assertRaisesRegex(DetachFailed, '连接状态未确认'):
            gate.run(Mock(side_effect=ValueError('challenge')))
        self.assertTrue(gate.waiting_for_user)
        operation = Mock()
        with self.assertRaisesRegex(RuntimeError, '等待用户'):
            gate.run(operation)
        operation.assert_not_called()
        detach.assert_called_once_with()

    def test_same_url_html_challenge_releases_without_input(self):
        page = PageBrowseTests().make_page()
        detach = Mock()
        gate = BrowserHandoff(detach)
        with self.assertRaisesRegex(ValueError, 'challenge'):
            gate.run(
                read_page_after_browsing, page, wheel_origin=(600, 300),
                check_html=Mock(side_effect=ValueError('challenge')),
            )
        detach.assert_called_once_with()
        page.mouse.move.assert_not_called()
        page.mouse.wheel.assert_not_called()

    def test_challenge_url_releases_without_reading_or_input(self):
        page = PageBrowseTests().make_page('https://shopee.ph/verify/captcha')
        detach = Mock()
        with self.assertRaises(BrowseInterrupted):
            BrowserHandoff(detach).run(
                read_page_after_browsing, page, wheel_origin=(600, 300), check_html=Mock(),
            )
        detach.assert_called_once_with()
        page.content.assert_not_called()
        page.evaluate.assert_not_called()
        page.mouse.wheel.assert_not_called()


class PageBrowseTests(unittest.TestCase):
    def make_page(self, url=STORE):
        return SimpleNamespace(
            url=url,
            is_closed=Mock(return_value=False),
            evaluate=Mock(return_value={'visibility': 'visible', 'focused': True}),
            content=Mock(side_effect=['before', 'after']),
            wait_for_timeout=Mock(),
            mouse=SimpleNamespace(move=Mock(), wheel=Mock()),
        )

    def browse(self, page, check=None, **kwargs):
        return read_page_after_browsing(
            page, wheel_origin=(600, 300), check_html=check or Mock(),
            rng=random.Random(17), **kwargs,
        )

    def test_only_final_dom_is_returned_after_checked_browsing(self):
        page = self.make_page()
        events = []
        page.mouse.wheel.side_effect = lambda x, y: events.append(('wheel', x, y))
        result = self.browse(page, lambda raw, url: events.append(('check', raw)))
        self.assertEqual((result.html, result.url), ('after', STORE))
        self.assertEqual(events[0], ('check', 'before'))
        self.assertEqual(events[-1], ('check', 'after'))
        self.assertGreaterEqual(len(result.wheel_deltas), 3)
        self.assertEqual(tuple(e[2] for e in events if e[0] == 'wheel'), result.wheel_deltas)
        self.assertTrue(all(e[1] == 0 for e in events if e[0] == 'wheel'))

    def test_challenge_login_and_unrelated_pages_receive_no_input(self):
        for url in (
            'https://shopee.ph/verify/captcha?private=value',
            'https://shopee.ph/buyer/login',
            'https://shopee.ph/product/123/456',
            'https://example.com/ugreen.ph',
        ):
            with self.subTest(url=url):
                page = self.make_page(url)
                with self.assertRaises(BrowseInterrupted) as error:
                    self.browse(page)
                self.assertNotIn('private=value', str(error.exception))
                page.content.assert_not_called()
                page.mouse.move.assert_not_called()
                page.mouse.wheel.assert_not_called()

    def test_same_url_challenge_detected_by_html_check_stops_before_input(self):
        page = self.make_page()
        with self.assertRaisesRegex(ValueError, 'challenge'):
            self.browse(page, Mock(side_effect=ValueError('challenge')))
        page.mouse.move.assert_not_called()
        page.mouse.wheel.assert_not_called()

    def test_hidden_or_unfocused_readable_page_continues(self):
        for state in (
            {'visibility': 'hidden', 'focused': True},
            {'visibility': 'visible', 'focused': False},
            {},
        ):
            with self.subTest(state=state):
                page = self.make_page()
                page.evaluate.return_value = state
                result = self.browse(page)
                self.assertEqual(result.html, 'after')
                self.assertEqual(page.content.call_count, 2)
                page.mouse.move.assert_called_once_with(600, 300)
                self.assertGreaterEqual(page.mouse.wheel.call_count, 3)
                page.evaluate.assert_not_called()

    def test_focus_loss_during_browsing_keeps_same_connection(self):
        for after_first_wheel in (False, True):
            with self.subTest(after_first_wheel=after_first_wheel):
                page = self.make_page()
                detach = Mock()
                gate = BrowserHandoff(detach)

                def lose_focus(_):
                    if not after_first_wheel or page.mouse.wheel.called:
                        page.evaluate.return_value = {'visibility': 'hidden', 'focused': False}

                page.wait_for_timeout.side_effect = lose_focus
                result = gate.run(self.browse, page)
                self.assertEqual(result.html, 'after')
                self.assertFalse(page.evaluate.return_value['focused'])
                self.assertGreaterEqual(page.mouse.wheel.call_count, 3)
                self.assertFalse(gate.waiting_for_user)
                detach.assert_not_called()

    def test_background_page_actual_input_failure_still_detaches(self):
        page = self.make_page()
        page.evaluate.return_value = {'visibility': 'hidden', 'focused': False}
        page.mouse.wheel.side_effect = TimeoutError('input timed out')
        detach = Mock()
        gate = BrowserHandoff(detach)
        with self.assertRaisesRegex(TimeoutError, 'input timed out'):
            gate.run(self.browse, page)
        detach.assert_called_once_with()
        self.assertTrue(gate.waiting_for_user)
        self.assertEqual(page.mouse.wheel.call_count, 1)
        self.assertEqual(page.content.call_count, 1)

    def test_redirect_during_wheel_wait_stops_without_more_input(self):
        page = self.make_page()

        def after_wait(_):
            if page.mouse.wheel.called:
                page.url = 'https://shopee.ph/verify/captcha'

        page.wait_for_timeout.side_effect = after_wait
        with self.assertRaises(BrowseInterrupted):
            self.browse(page)
        self.assertEqual(page.mouse.wheel.call_count, 1)
        self.assertEqual(page.content.call_count, 1)

    def test_manual_navigation_to_another_product_stops(self):
        page = self.make_page()
        page.wait_for_timeout.side_effect = lambda _: setattr(
            page, 'url', 'https://shopee.ph/product/64922227/1159521988'
        )
        with self.assertRaises(BrowseInterrupted):
            self.browse(page)
        page.mouse.wheel.assert_not_called()

    def test_final_html_challenge_is_not_returned_as_success(self):
        page = self.make_page()

        def check(raw, _):
            if raw == 'after':
                raise ValueError('challenge after browsing')

        with self.assertRaisesRegex(ValueError, 'challenge after'):
            self.browse(page, check)
        self.assertEqual(page.content.call_count, 2)

    def test_wheel_failure_is_propagated_without_retry_or_final_capture(self):
        page = self.make_page()
        page.mouse.wheel.side_effect = RuntimeError('input failed')
        with self.assertRaisesRegex(RuntimeError, 'input failed'):
            self.browse(page)
        self.assertEqual(page.mouse.wheel.call_count, 1)
        self.assertEqual(page.content.call_count, 1)

    def test_closed_page_receives_no_input(self):
        page = self.make_page()
        page.is_closed.return_value = True
        with self.assertRaises(BrowseInterrupted):
            self.browse(page)
        page.mouse.wheel.assert_not_called()


if __name__ == '__main__':
    unittest.main()
