"""scanner.py — Scans and deduplicates nearby Wi-Fi access points via nmcli."""
from __future__ import annotations

import logging
from typing import Any

from src.devices.wifi.runner import (
    SIMULATION_STATE,
    get_wifi_interface,
    is_nmcli_available,
    run_nmcli,
)

logger = logging.getLogger(__name__)


def _parse_nmcli_line(line: str) -> dict[str, Any] | None:
    parts = line.strip().split(":")
    if len(parts) < 5: return None
    in_use = parts[0].strip() == "*"
    ssid = parts[1].replace("\\:", ":").strip()
    if not ssid: return None
    try: sig = int(parts[2])
    except ValueError: sig = 0
    return {"in_use": in_use, "ssid": ssid, "signal": sig, "security": parts[3].strip() or "Open", "bars": parts[4].strip()}


def scan_networks(iface: str | None = None) -> list[dict[str, Any]]:
    """Scan nearby Wi-Fi networks and return deduplicated list sorted by signal."""
    if not is_nmcli_available() or SIMULATION_STATE["enabled"]:
        return [
            {"in_use": True, "ssid": "Office_5G", "signal": 90, "security": "WPA2", "bars": "▂▄▆█"},
            {"in_use": False, "ssid": "Guest_Net", "signal": 65, "security": "WPA2", "bars": "▂▄▆_"},
            {"in_use": False, "ssid": "Warehouse_IoT", "signal": 45, "security": "WPA-PSK", "bars": "▂▄__"},
        ]
    dev = iface or get_wifi_interface()
    code, out = run_nmcli(["-t", "-f", "IN-USE,SSID,SIGNAL,SECURITY,BARS", "device", "wifi", "list", "ifname", dev, "--rescan", "yes"])
    if code != 0:
        _, out = run_nmcli(["-t", "-f", "IN-USE,SSID,SIGNAL,SECURITY,BARS", "device", "wifi", "list"])
    results: dict[str, dict[str, Any]] = {}
    for line in out.splitlines():
        item = _parse_nmcli_line(line)
        if item and (item["ssid"] not in results or item["signal"] > results[item["ssid"]]["signal"]):
            results[item["ssid"]] = item
    return sorted(results.values(), key=lambda x: int(x["signal"]), reverse=True)


def get_available_networks() -> list[dict[str, Any]]:
    """Public Hermes API adapter for scanning nearby networks."""
    return scan_networks()


__all__ = ["get_available_networks", "scan_networks"]
