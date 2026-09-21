"""Segmented wheel browsing on an already attached, verified Shopee page.

No browser launch, environment overrides, JavaScript scrolling, or persistence.
This adds visible browsing; it does not promise acceptance by website risk controls.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
import random
import re
from typing import Callable
from urllib.parse import urlsplit

from list_html import _identity
from pacing import paced_wait_seconds


class BrowseInterrupted(RuntimeError):
    """The bound page closed, changed, or is no longer an eligible page."""


class CaptchaDetected(BrowseInterrupted):
    """Observed CAPTCHA / human verification that requires user intervention."""


class DetachFailed(RuntimeError):
    """Collection stopped, but releasing the connection was not confirmed."""


class BrowserHandoff:
    """Release control for actual CAPTCHA or explicit stop, not ordinary errors.

    The host supplies pw.stop for its existing CDP attachment, never browser.close,
    and wraps navigation, browsing, parsing and the enclosing capture loop in run.
    Ordinary timeout/read/parse exceptions propagate to the host for automatic
    recovery on the same attachment. They never lock waiting_for_user.
    CAPTCHA detection must raise CaptchaDetected; after that, never auto-resume.
    """

    def __init__(self, detach: Callable[[], None], *, on_handoff: Callable[[], object] | None = None):
        if not callable(detach):
            raise TypeError("detach 必须是只断开附着连接的回调")
        self._detach = detach
        self._on_handoff = on_handoff
        self.waiting_for_user = False

    def run(self, operation, *args, **kwargs):
        if self.waiting_for_user:
            raise RuntimeError("已停止采集，等待用户明确回复继续；禁止自动重连")
        try:
            return operation(*args, **kwargs)
        except (CaptchaDetected, KeyboardInterrupt, SystemExit):
            if not self.waiting_for_user:
                self.waiting_for_user = True
                detach_error = None
                try:
                    self._detach()
                except BaseException as error:
                    detach_error = error
                try:
                    if self._on_handoff is not None:
                        self._on_handoff()
                except BaseException as error:
                    state = "连接状态未确认" if detach_error else "连接已断开"
                    raise RuntimeError(f"采集已停止，{state}；尾批 Excel 保存失败") from error
                if detach_error is not None:
                    raise DetachFailed("采集已停止，但自动断开失败，连接状态未确认") from detach_error
            raise


@dataclass(frozen=True)
class BrowsedPage:
    html: str
    url: str
    wheel_deltas: tuple[int, ...]


def _guard_page(page, expected_url: str) -> None:
    if page.is_closed():
        raise BrowseInterrupted("滚动页面已关闭")
    current = page.url
    parts = urlsplit(current)
    if parts.hostname == "shopee.ph" and re.search(r"/(?:verify|captcha)(?:/|$)", parts.path, re.I):
        raise CaptchaDetected("检测到验证码/人工验证，保留原页：" + parts.path)
    identity = _identity(current)
    valid = (
        parts.scheme == "https" and parts.hostname == "shopee.ph"
        and not parts.username and not parts.password and parts.port is None
        and (parts.path.rstrip("/") == "/ugreen.ph"
             or (identity is not None and identity[0] == "64922227"))
    )
    if not valid or current != expected_url:
        raise BrowseInterrupted("页面身份改变或非商品/店铺页，宿主核对后恢复：" + parts.path)


def read_page_after_browsing(
    page,
    *,
    wheel_origin: tuple[float, float],
    check_html: Callable[[str, str], object],
    rng: random.Random | None = None,
) -> BrowsedPage:
    """Check the rendered page, browse with wheel events, then capture final DOM.

    The caller binds the existing tab and provides an observed point inside its
    content viewport. check_html must reject challenges/incomplete documents.
    The first DOM is a pre-scroll safety check; only the final DOM is handed to
    business parsers. Wheel deltas describe dispatched input, not measured motion.
    Background visibility or missing focus does not interrupt collection. Actual
    read/input failures propagate for automatic host recovery. The host may bound
    stalled input calls, then check fresh DOM before deciding whether to retry.
    check_html raises CaptchaDetected only for observed human verification;
    ordinary errors do not detach or require user confirmation.
    """
    if (len(wheel_origin) != 2 or any(
        isinstance(x, bool) or not isinstance(x, (int, float))
        or not math.isfinite(x) or x <= 0 for x in wheel_origin
    )):
        raise ValueError("wheel_origin 必须是已核对的内容视口内坐标")
    rng = rng if rng is not None else random.SystemRandom()
    expected_url = page.url
    _guard_page(page, expected_url)

    def pause(low: float, high: float) -> None:
        page.wait_for_timeout(paced_wait_seconds(rng.uniform(low, high)) * 1000)
        _guard_page(page, expected_url)

    pause(2.0, 4.0)
    before = page.content()
    check_html(before, page.url)
    _guard_page(page, expected_url)
    page.mouse.move(*wheel_origin)
    deltas = []
    down_count = rng.randint(3, 5)
    back_after = rng.randint(1, down_count - 1) if rng.random() < 0.35 else None
    for index in range(down_count):
        _guard_page(page, expected_url)
        delta = rng.randint(280, 560)
        page.mouse.wheel(0, delta)
        deltas.append(delta)
        pause(0.9, 2.4)
        if index == back_after:
            delta = -rng.randint(100, 220)
            page.mouse.wheel(0, delta)
            deltas.append(delta)
            pause(1.0, 2.0)
    pause(1.2, 2.5)
    final_html = page.content()
    check_html(final_html, page.url)
    _guard_page(page, expected_url)
    return BrowsedPage(final_html, page.url, tuple(deltas))
