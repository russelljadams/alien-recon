"""Ghost Girl — network utilities."""

import subprocess
import socket
import re


def get_vpn_ip(interface="tun0"):
    """Get the IP address assigned to the VPN interface."""
    try:
        result = subprocess.run(
            ["ip", "-4", "addr", "show", interface],
            capture_output=True, text=True, timeout=5
        )
        match = re.search(r"inet (\d+\.\d+\.\d+\.\d+)", result.stdout)
        if match:
            return match.group(1)
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return None


def check_vpn_status(interface="tun0"):
    """Check if VPN interface is up and has an IP."""
    ip = get_vpn_ip(interface)
    return ip is not None, ip


def get_local_ip():
    """Get the primary local IP (non-loopback)."""
    try:
        # Connect to a public DNS to determine our outbound IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(2)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except OSError:
        return "127.0.0.1"


def is_port_open(host, port, timeout=3):
    """Quick TCP connect check."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        result = s.connect_ex((host, int(port)))
        s.close()
        return result == 0
    except OSError:
        return False
