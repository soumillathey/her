"""watchdog.py — Flap-debounced background Wi-Fi connectivity watchdog."""
from __future__ import annotations

import logging
import threading
import time

from src.devices.wifi.activity import is_nmcli_busy, is_watchdog_suspended
from src.devices.wifi.connectivity import is_network_connected
from src.devices.wifi.constants import (
    DEFAULT_FAILURE_THRESHOLD,
    DEFAULT_WIFI_WATCHDOG_INTERVAL,
)
from src.devices.wifi.hotspot import (
    is_hotspot_active,
    start_emergency_hotspot,
    stop_emergency_hotspot,
)

logger = logging.getLogger(__name__)
_watchdog_thread: threading.Thread | None = None
_running = False


def _watchdog_loop(interval: float = DEFAULT_WIFI_WATCHDOG_INTERVAL, threshold: int = DEFAULT_FAILURE_THRESHOLD) -> None:
    fails = 0
    while _running:
        time.sleep(interval)
        if not _running or is_watchdog_suspended() or is_nmcli_busy(): continue
        if is_network_connected():
            fails = 0
            if is_hotspot_active():
                logger.info("[Watchdog] Internet restored. Stopping emergency hotspot...")
                stop_emergency_hotspot()
        else:
            fails += 1
            if fails >= threshold and not is_hotspot_active():
                logger.warning("[Watchdog] Wi-Fi lost (%d fails). Activating hotspot...", fails)
                start_emergency_hotspot()


def start_wifi_watchdog(interval: float = DEFAULT_WIFI_WATCHDOG_INTERVAL) -> bool:
    global _watchdog_thread, _running
    if _running and _watchdog_thread and _watchdog_thread.is_alive(): return True
    _running = True
    _watchdog_thread = threading.Thread(target=_watchdog_loop, args=(interval,), name="WiFiWatchdog", daemon=True)
    _watchdog_thread.start()
    logger.info("[Watchdog] Started Wi-Fi connectivity watchdog (interval=%.1fs)", interval)
    return True


def stop_wifi_watchdog() -> None:
    global _running, _watchdog_thread
    _running = False
    if _watchdog_thread and _watchdog_thread.is_alive(): _watchdog_thread.join(timeout=2.0)
    _watchdog_thread = None


def is_watchdog_running() -> bool:
    return bool(_running and _watchdog_thread and _watchdog_thread.is_alive())
