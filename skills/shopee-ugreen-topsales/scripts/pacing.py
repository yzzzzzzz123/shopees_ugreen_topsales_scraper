"""Scale deliberate collection waits, never browser deadlines or safety checks."""
from __future__ import annotations

import math


PACING_SPEED_MULTIPLIER = 2.5


def paced_wait_seconds(baseline_seconds: float) -> float:
    """Convert a pre-speedup wait once; actual page/network time is unscaled."""
    if (isinstance(baseline_seconds, bool)
            or not isinstance(baseline_seconds, (int, float))
            or not math.isfinite(baseline_seconds) or baseline_seconds < 0):
        raise ValueError("等待秒数必须是有限非负数")
    return baseline_seconds / PACING_SPEED_MULTIPLIER
