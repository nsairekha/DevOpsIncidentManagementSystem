"""Small shared helpers: UTC timestamps and latency simulation."""

import time
from datetime import datetime, timezone


def utc_now_iso() -> str:
    """Return the current UTC time as an ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat()


def apply_simulated_latency(latency_ms: int) -> None:
    """Block for ``latency_ms`` milliseconds (0 disables the delay).

    Used to inject controlled processing delays for later latency-anomaly
    experiments. Raises ValueError for negative values.
    """
    if latency_ms < 0:
        raise ValueError("latency_ms must be >= 0")
    if latency_ms > 0:
        time.sleep(latency_ms / 1000.0)