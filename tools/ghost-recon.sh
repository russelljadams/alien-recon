#!/usr/bin/env bash
# Ghost Girl — Session setup & automated reconnaissance
# Usage: ghost-recon.sh <TARGET_IP> <ROOM_NAME> [--hostname <HOST>]

set -euo pipefail

# ── Colors & Output ──────────────────────────────────────────────
RED='\033[91m'; GREEN='\033[92m'; YELLOW='\033[93m'
BLUE='\033[94m'; MAGENTA='\033[95m'; CYAN='\033[96m'
BOLD='\033[1m'; RESET='\033[0m'

status()  { echo -e "${BLUE}[*]${RESET} $1"; }
success() { echo -e "${GREEN}[+]${RESET} $1"; }
error()   { echo -e "${RED}[-]${RESET} $1" >&2; }
warning() { echo -e "${YELLOW}[!]${RESET} $1"; }
data()    { echo "[DATA] $1=$2"; }

banner() {
    echo -e "\n${MAGENTA}  ╔════════════════════════════════════════╗${RESET}"
    echo -e "${MAGENTA}  ║${RESET}       ${BOLD}Ghost Recon — Session Setup${RESET}       ${MAGENTA}║${RESET}"
    echo -e "${MAGENTA}  ╚════════════════════════════════════════╝${RESET}\n"
}

# ── Argument parsing ─────────────────────────────────────────────
usage() {
    echo "Usage: $0 <TARGET_IP> <ROOM_NAME> [--hostname <HOST>]"
    echo ""
    echo "  TARGET_IP    Target machine IP address"
    echo "  ROOM_NAME    TryHackMe/HackTheBox room name (used for session dir)"
    echo "  --hostname   Optional hostname to add to /etc/hosts"
    exit 1
}

[[ $# -lt 2 ]] && usage

TARGET_IP="$1"
ROOM_NAME="$2"
HOSTNAME=""
shift 2

while [[ $# -gt 0 ]]; do
    case "$1" in
        --hostname) HOSTNAME="$2"; shift 2 ;;
        *) error "Unknown option: $1"; usage ;;
    esac
done

# Validate IP format
if ! [[ "$TARGET_IP" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    error "Invalid IP address: $TARGET_IP"
    exit 1
fi

# ── Paths ────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DATE="$(date +%Y-%m-%d)"
SESSION_NAME="${DATE}-${ROOM_NAME}"
SESSION_DIR="${PROJECT_ROOT}/sessions/${SESSION_NAME}"
TEMPLATE="${PROJECT_ROOT}/sessions/.template.md"

banner

# ── VPN Check ────────────────────────────────────────────────────
status "Checking VPN connection..."
ATTACK_IP=$(ip -4 addr show tun0 2>/dev/null | grep -oP 'inet \K[\d.]+' || true)

if [[ -z "$ATTACK_IP" ]]; then
    warning "VPN (tun0) not detected — using local IP"
    ATTACK_IP=$(ip route get 8.8.8.8 2>/dev/null | grep -oP 'src \K[\d.]+' || echo "127.0.0.1")
    warning "Attack IP: ${ATTACK_IP}"
else
    success "VPN connected — Attack IP: ${ATTACK_IP}"
fi
data "ATTACK_IP" "$ATTACK_IP"
data "TARGET_IP" "$TARGET_IP"

# ── Session Directory ────────────────────────────────────────────
status "Setting up session directory..."

if [[ -d "$SESSION_DIR" ]]; then
    warning "Session directory already exists: ${SESSION_DIR}"
else
    mkdir -p "$SESSION_DIR"
    success "Created: ${SESSION_DIR}"
fi
data "SESSION_DIR" "$SESSION_DIR"

# Create session.md from template
SESSION_FILE="${SESSION_DIR}/session.md"
if [[ ! -f "$SESSION_FILE" ]]; then
    if [[ -f "$TEMPLATE" ]]; then
        sed -e "s/<ROOM_NAME>/${ROOM_NAME}/g" \
            -e "s/YYYY-MM-DD/${DATE}/g" \
            -e "s/<IP>/${TARGET_IP}/g" \
            "$TEMPLATE" > "$SESSION_FILE"
        success "Created session file from template"
    else
        warning "Template not found at ${TEMPLATE} — creating minimal session file"
        cat > "$SESSION_FILE" <<EOF
# Session: ${ROOM_NAME}

**Date:** ${DATE}
**Target IP:** ${TARGET_IP}
**Attack IP:** ${ATTACK_IP}

---

## Recon

## Enumeration

## Exploitation

## Privilege Escalation

## Flags

- [ ] User flag:
- [ ] Root flag:

## Lessons Learned
EOF
        success "Created minimal session file"
    fi
else
    warning "Session file already exists, skipping"
fi

# ── /etc/hosts ───────────────────────────────────────────────────
if [[ -n "$HOSTNAME" ]]; then
    status "Configuring /etc/hosts for ${HOSTNAME}..."
    HOSTS_ENTRY="${TARGET_IP} ${HOSTNAME}"

    if grep -qF "$HOSTNAME" /etc/hosts 2>/dev/null; then
        # Check if it points to the right IP
        EXISTING=$(grep -F "$HOSTNAME" /etc/hosts | head -1)
        if echo "$EXISTING" | grep -qF "$TARGET_IP"; then
            warning "Entry already exists: ${EXISTING}"
        else
            warning "Hostname exists with different IP: ${EXISTING}"
            warning "Updating to: ${HOSTS_ENTRY}"
            sudo sed -i "/${HOSTNAME}/d" /etc/hosts
            echo "$HOSTS_ENTRY" | sudo tee -a /etc/hosts >/dev/null
            success "Updated /etc/hosts"
        fi
    else
        echo "$HOSTS_ENTRY" | sudo tee -a /etc/hosts >/dev/null
        success "Added to /etc/hosts: ${HOSTS_ENTRY}"
    fi
    data "HOSTNAME" "$HOSTNAME"
fi

# ── Nmap Scans ───────────────────────────────────────────────────
NMAP_INITIAL="${SESSION_DIR}/nmap-initial.txt"
NMAP_FULL="${SESSION_DIR}/nmap-full.txt"

# Initial scan (-sC -sV)
status "Running initial nmap scan (-sC -sV)..."
nmap -sC -sV -oN "$NMAP_INITIAL" "$TARGET_IP" 2>/dev/null

if [[ -f "$NMAP_INITIAL" ]]; then
    success "Initial scan complete: ${NMAP_INITIAL}"

    # Parse open ports into a table
    echo -e "\n${CYAN}─── Open Ports ─────────────────────────────────────${RESET}"
    printf "  ${BOLD}%-8s %-12s %-12s %s${RESET}\n" "PORT" "STATE" "SERVICE" "VERSION"
    echo "  ──────── ──────────── ──────────── ─────────────────────────"

    OPEN_PORTS=""
    while IFS= read -r line; do
        PORT=$(echo "$line" | awk -F'/' '{print $1}')
        PROTO=$(echo "$line" | awk -F'/' '{print $2}' | awk '{print $1}')
        STATE=$(echo "$line" | awk '{print $2}')
        SERVICE=$(echo "$line" | awk '{print $3}')
        VERSION=$(echo "$line" | awk '{for(i=4;i<=NF;i++) printf "%s ", $i; print ""}' | sed 's/ *$//')
        printf "  %-8s %-12s %-12s %s\n" "${PORT}/${PROTO}" "$STATE" "$SERVICE" "$VERSION"
        OPEN_PORTS="${OPEN_PORTS}${PORT}/${PROTO},"
    done < <(grep -E "^[0-9]+/[a-z]+" "$NMAP_INITIAL" | grep "open")

    OPEN_PORTS="${OPEN_PORTS%,}"  # Remove trailing comma
    echo ""
    data "OPEN_PORTS" "$OPEN_PORTS"
else
    error "Initial nmap scan failed"
fi

# Full port scan in background
status "Kicking off full port scan (-p- -T4) in background..."
nmap -p- -T4 -oN "$NMAP_FULL" "$TARGET_IP" 2>/dev/null &
NMAP_BG_PID=$!
success "Full scan running (PID: ${NMAP_BG_PID}) → ${NMAP_FULL}"
data "NMAP_FULL_PID" "$NMAP_BG_PID"

# ── Summary ──────────────────────────────────────────────────────
echo -e "\n${CYAN}─── Session Ready ──────────────────────────────────${RESET}"
echo -e "  Target:     ${BOLD}${TARGET_IP}${RESET}"
echo -e "  Attack IP:  ${BOLD}${ATTACK_IP}${RESET}"
[[ -n "$HOSTNAME" ]] && echo -e "  Hostname:   ${BOLD}${HOSTNAME}${RESET}"
echo -e "  Session:    ${BOLD}${SESSION_DIR}${RESET}"
echo -e "  Nmap:       ${BOLD}${NMAP_INITIAL}${RESET}"
echo -e "  Full scan:  ${BOLD}running in background (PID ${NMAP_BG_PID})${RESET}"
echo ""
success "Recon phase initialized. Review nmap results and plan next steps."
