"""connection.py — Connects device to facility Wi-Fi networks via nmcli."""
from __future__ import annotations

import logging
import sqlite3

from src.core.wifi_vault import save_wifi_network
from src.devices.wifi.activity import suspend_watchdog
from src.devices.wifi.hotspot import (
    is_hotspot_active,
    start_emergency_hotspot,
    stop_hotspot,
)
from src.devices.wifi.runner import (
    SIMULATION_STATE,
    get_wifi_interface,
    is_nmcli_available,
    run_nmcli,
)

logger = logging.getLogger(__name__)


def get_active_wifi_ssid(iface: str | None = None) -> str | None:
    if not is_nmcli_available() or SIMULATION_STATE["enabled"]:
        return str(SIMULATION_STATE.get("active_ssid", ""))
    dev = iface or get_wifi_interface()
    code, out = run_nmcli(["-t", "-f", "NAME,DEVICE", "connection", "show", "--active"])
    if code != 0: return None
    for line in out.splitlines():
        parts = line.split(":")
        if len(parts) >= 2 and parts[1].strip() == dev and not parts[0].strip().endswith("-hotspot"):
            return parts[0].strip()
    return None


def get_existing_profile(ssid: str) -> bool:
    if not is_nmcli_available() or SIMULATION_STATE["enabled"]: return True
    code, out = run_nmcli(["-t", "-f", "NAME", "connection", "show"])
    return code == 0 and ssid in [line.strip() for line in out.splitlines()]


def connect_wifi(ssid: str, password: str = "", iface: str | None = None) -> tuple[bool, str]:
    if not ssid.strip(): return False, "SSID cannot be empty"
    suspend_watchdog(25.0); stop_hotspot()
    if not is_nmcli_available() or SIMULATION_STATE["enabled"]:
        SIMULATION_STATE["active_ssid"] = ssid; return True, f"Connected to '{ssid}'"
    dev = iface or get_wifi_interface()
    run_nmcli(["connection", "delete", ssid])
    cmd = ["device", "wifi", "connect", ssid, "ifname", dev]
    if password: cmd.extend(["password", password])
    code, out = run_nmcli(cmd, timeout=30.0)
    return (True, f"Successfully connected to '{ssid}'") if code == 0 else (False, f"Connection failed: {out}")


def connect_to_wifi(ssid: str, password: str = "", iface: str | None = None) -> tuple[bool, str]:
    was_hotspot = is_hotspot_active()
    ok, msg = connect_wifi(ssid, password, iface)
    if ok:
        try: save_wifi_network(ssid, password)
        except (sqlite3.Error, OSError) as e: logger.warning("Failed to save to vault: %s", e)
        return True, msg
    if was_hotspot: start_emergency_hotspot()
    return False, msg
