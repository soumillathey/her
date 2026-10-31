"""connectivity.py — Probes internet connectivity via low-latency DNS socket."""
from __future__ import annotations

import socket

CHECK_TARGETS = (("1.1.1.1", 53), ("8.8.8.8", 53))


def is_network_connected(timeout: float = 2.0) -> bool:
    """Probes remote DNS servers to verify live internet route."""
    for host, port in CHECK_TARGETS:
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except (OSError, TimeoutError): continue
    return False


def is_wifi_connected(timeout: float = 2.0) -> bool:
    """Hermes compatibility alias for checking internet connectivity."""
    return is_network_connected(timeout)


__all__ = ["is_network_connected", "is_wifi_connected"]
