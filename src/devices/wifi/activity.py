"""activity.py — Thread synchronization and watchdog suspension tracker."""
from __future__ import annotations

import logging
import threading
import time

logger = logging.getLogger(__name__)

nmcli_lock = threading.RLock()
_activity_lock = threading.Lock()
_suspended_until = 0.0


def suspend_watchdog(seconds: float = 10.0) -> None:
    """Temporarily pause watchdog failure checks during critical transitions."""
    global _suspended_until
    with _activity_lock:
        now = time.monotonic()
        _suspended_until = max(_suspended_until, now + seconds)
        logger.info("[Watchdog] Connectivity checks suspended for %.1fs", seconds)


def is_watchdog_suspended() -> bool:
    """Check if watchdog is currently in a cooldown suspension window."""
    with _activity_lock:
        return time.monotonic() < _suspended_until


def is_nmcli_busy() -> bool:
    """Returns True if any nmcli operation is currently holding the execution lock."""
    if nmcli_lock.acquire(blocking=False):
        nmcli_lock.release()
        return False
    return True


__all__ = ["is_nmcli_busy", "is_watchdog_suspended", "nmcli_lock", "suspend_watchdog"]
