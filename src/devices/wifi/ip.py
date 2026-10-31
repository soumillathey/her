"""ip.py — Resolves active hotspot gateway IP for the wireless interface."""
from __future__ import annotations

import subprocess


def get_hotspot_ip(iface: str = "wlan0") -> str:
    """Retrieve assigned IP address on hotspot interface."""
    try:
        out = subprocess.check_output(["ip", "-4", "addr", "show", iface], text=True, stderr=subprocess.DEVNULL)
        for line in out.splitlines():
            line = line.strip()
            if line.startswith("inet "):
                return line.split()[1].split("/")[0]
    except (subprocess.SubprocessError, OSError): pass
    return "10.42.0.1"


__all__ = ["get_hotspot_ip"]
