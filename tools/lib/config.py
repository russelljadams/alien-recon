"""Ghost Girl — shared configuration and paths."""

import os

# Project root is two levels up from this file (tools/lib/config.py -> project root)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Key directories
SESSIONS_DIR = os.path.join(PROJECT_ROOT, "sessions")
TOOLS_DIR = os.path.join(PROJECT_ROOT, "tools")
EXPLOITS_DIR = os.path.join(TOOLS_DIR, "exploits")
KNOWLEDGE_DIR = os.path.join(PROJECT_ROOT, "knowledge")
DIRECTIVES_DIR = os.path.join(PROJECT_ROOT, "directives")

# Session template
SESSION_TEMPLATE = os.path.join(SESSIONS_DIR, ".template.md")

# Wordlists
WORDLISTS = {
    "rockyou": "/usr/share/wordlists/rockyou.txt",
    "dirb_common": "/usr/share/wordlists/dirb/common.txt",
    "dirbuster_medium": "/usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt",
    "seclists_dns": "/usr/share/wordlists/seclists/Discovery/DNS/subdomains-top1million-5000.txt",
}

# Default ports / settings
DEFAULT_LPORT = 4444
DEFAULT_HTTP_PORT = 8000
NMAP_INITIAL_FLAGS = "-sC -sV"
NMAP_FULL_FLAGS = "-p- -T4"

# VPN interface
VPN_INTERFACE = "tun0"

# Ghost-listen socket path
LISTEN_SOCKET = "/tmp/ghost-listen.sock"

# Output delimiter prefix for machine-parseable lines
DATA_PREFIX = "[DATA]"
