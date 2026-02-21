#!/usr/bin/env python3
"""Ghost Girl — Post-exploitation enumeration orchestrator.

Uploads and runs ghost-enum-target.sh on the target, then parses
and highlights privilege escalation vectors.

Usage:
  # Via ghost-listen (target already has a shell)
  python3 ghost-enum.py

  # Via SSH
  python3 ghost-enum.py --ssh user:password@host

  # Parse saved output offline
  python3 ghost-enum.py --parse enum-output.txt

  # Save raw output
  python3 ghost-enum.py --save session-dir/enum-raw.txt
"""

import argparse
import os
import re
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, PROJECT_ROOT)

from tools.lib.output import banner, status, success, error, warning, data, section, table
from tools.lib.config import LISTEN_SOCKET

ENUM_SCRIPT = os.path.join(SCRIPT_DIR, "enumscripts", "ghost-enum-target.sh")

# Known GTFOBins SUID binaries that can be exploited for privesc
GTFOBINS_SUID = {
    "ar", "aria2c", "ash", "awk", "base32", "base64", "bash", "bridge",
    "busybox", "cat", "chmod", "chown", "cp", "csh", "curl", "cut",
    "dash", "dd", "dialog", "diff", "dig", "docker", "dmsetup", "ed",
    "emacs", "env", "eqn", "expand", "expect", "file", "find", "flock",
    "fmt", "fold", "gawk", "gdb", "gimp", "grep", "gtester", "hd",
    "head", "hexdump", "highlight", "iconv", "install", "ionice",
    "ip", "jjs", "join", "jq", "jrunscript", "ksh", "ld.so", "less",
    "logsave", "look", "lua", "make", "mawk", "more", "mv", "nano",
    "nawk", "nice", "nl", "nmap", "node", "nohup", "od", "openssl",
    "paste", "perl", "pg", "php", "pic", "pico", "python", "python2",
    "python3", "readelf", "restic", "rev", "rlwrap", "rpm", "rpmquery",
    "rsync", "run-parts", "rvim", "sed", "setarch", "shuf", "socat",
    "sort", "start-stop-daemon", "stdbuf", "strace", "strings", "sysctl",
    "systemctl", "tac", "tail", "taskset", "tclsh", "tee", "tftp",
    "time", "timeout", "ul", "unexpand", "uniq", "unshare", "vim",
    "vimdiff", "watch", "wc", "wget", "whois", "wish", "xargs",
    "xxd", "zip", "zsh",
}

# Standard SUID binaries that are expected/safe
STANDARD_SUID = {
    "su", "sudo", "passwd", "mount", "umount", "chfn", "chsh", "newgrp",
    "gpasswd", "pkexec", "ping", "ping6", "traceroute", "fusermount",
    "fusermount3", "ntfs-3g", "vmware-user-suid-wrapper", "pppd",
    "Xorg", "ssh-keysign", "dbus-daemon-launch-helper",
    "unix_chkpwd", "at", "crontab",
}


def parse_sections(raw_text):
    """Parse ---SECTION:name--- delimited output into a dict."""
    sections = {}
    current = None
    lines = []

    for line in raw_text.split('\n'):
        match = re.match(r'^---SECTION:(\w+)---$', line.strip())
        if match:
            if current is not None:
                sections[current] = '\n'.join(lines)
            current = match.group(1)
            lines = []
        elif current is not None:
            lines.append(line)

    if current is not None:
        sections[current] = '\n'.join(lines)

    return sections


def analyze_suid(suid_text):
    """Analyze SUID binaries for privesc vectors."""
    findings = []
    binaries = [line.strip() for line in suid_text.strip().split('\n') if line.strip()]

    for binary_path in binaries:
        binary_name = os.path.basename(binary_path)
        if binary_name in GTFOBINS_SUID:
            findings.append(("CRITICAL", binary_path, f"GTFOBins SUID — {binary_name}"))
        elif binary_name not in STANDARD_SUID:
            findings.append(("UNUSUAL", binary_path, "Non-standard SUID binary"))

    return findings


def analyze_sudo(sudo_text):
    """Analyze sudo -l output for privesc vectors."""
    findings = []
    if "NOPASSWD" in sudo_text:
        for line in sudo_text.split('\n'):
            if "NOPASSWD" in line:
                findings.append(("CRITICAL", line.strip(), "NOPASSWD sudo entry"))

    if "(ALL" in sudo_text and "ALL)" in sudo_text:
        findings.append(("CRITICAL", "sudo -l", "User may run ALL commands"))

    # Check for specific exploitable commands
    exploitable = ["vim", "vi", "nano", "less", "more", "find", "awk", "python",
                    "python3", "perl", "ruby", "bash", "sh", "env", "nmap",
                    "ftp", "tar", "zip", "man", "git", "tee"]
    for prog in exploitable:
        if re.search(rf'\b{prog}\b', sudo_text):
            findings.append(("HIGH", f"sudo {prog}", f"Potentially exploitable via GTFOBins"))

    return findings


def analyze_capabilities(cap_text):
    """Analyze file capabilities for privesc."""
    findings = []
    dangerous_caps = {
        "cap_setuid": "Can set UID — direct privesc",
        "cap_setgid": "Can set GID",
        "cap_dac_override": "Bypasses file permission checks",
        "cap_dac_read_search": "Bypasses file read permission",
        "cap_net_raw": "Can create raw sockets (packet sniffing)",
        "cap_sys_admin": "Broad admin capabilities",
        "cap_sys_ptrace": "Can trace/debug processes",
    }

    for line in cap_text.strip().split('\n'):
        if not line.strip():
            continue
        for cap, desc in dangerous_caps.items():
            if cap in line.lower():
                findings.append(("HIGH", line.strip(), desc))
                break

    return findings


def analyze_cron(cron_text):
    """Check for writable cron jobs."""
    findings = []
    # Look for script paths in cron entries
    for line in cron_text.split('\n'):
        line = line.strip()
        if not line or line.startswith('#') or line.startswith('='):
            continue
        # Extract potential file paths
        paths = re.findall(r'(/\S+)', line)
        for path in paths:
            if path.startswith(('/usr/', '/bin/', '/sbin/', '/dev/')):
                continue
            if os.path.exists(path) and os.access(path, os.W_OK):
                findings.append(("CRITICAL", path, "Writable cron job script"))

    return findings


def analyze_and_report(sections):
    """Analyze all sections and print findings."""
    all_findings = []

    # Identity
    if "identity" in sections:
        section("Identity")
        for line in sections["identity"].strip().split('\n'):
            if line.strip():
                print(f"  {line.strip()}")
        uid_match = re.search(r'UID=(\d+)', sections["identity"])
        if uid_match and uid_match.group(1) == "0":
            success("Already root!")
            data("IS_ROOT", "true")
            return

    # System info
    if "system" in sections:
        section("System")
        for line in sections["system"].strip().split('\n')[:5]:
            if line.strip():
                print(f"  {line.strip()}")
        # Check for old kernels
        kernel_match = re.search(r'KERNEL=(.+)', sections["system"])
        if kernel_match:
            data("KERNEL", kernel_match.group(1).strip())

    # Sudo analysis
    if "sudo" in sections:
        section("Sudo Privileges")
        findings = analyze_sudo(sections["sudo"])
        if findings:
            all_findings.extend(findings)
            for severity, item, desc in findings:
                color_fn = success if severity == "CRITICAL" else warning
                color_fn(f"[{severity}] {desc}: {item}")
        else:
            print("  No exploitable sudo entries found")

    # SUID analysis
    if "suid" in sections:
        section("SUID Binaries")
        findings = analyze_suid(sections["suid"])
        if findings:
            all_findings.extend(findings)
            for severity, item, desc in findings:
                color_fn = success if severity == "CRITICAL" else warning
                color_fn(f"[{severity}] {desc}: {item}")
        binaries = [l.strip() for l in sections["suid"].strip().split('\n') if l.strip()]
        data("SUID_COUNT", str(len(binaries)))

    # Capabilities
    if "capabilities" in sections:
        section("Capabilities")
        findings = analyze_capabilities(sections["capabilities"])
        if findings:
            all_findings.extend(findings)
            for severity, item, desc in findings:
                warning(f"[{severity}] {desc}: {item}")
        elif sections["capabilities"].strip():
            print("  No dangerous capabilities found")

    # Cron
    if "cron" in sections:
        section("Cron Jobs")
        findings = analyze_cron(sections["cron"])
        if findings:
            all_findings.extend(findings)
            for severity, item, desc in findings:
                success(f"[{severity}] {desc}: {item}")
        # Show cron content summary
        for line in sections["cron"].strip().split('\n'):
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('==='):
                print(f"  {line}")

    # Network
    if "network" in sections:
        section("Network (Listening)")
        for line in sections["network"].split('\n'):
            if "LISTEN" in line or "State" in line:
                print(f"  {line.strip()}")

    # Interesting files
    if "interesting_files" in sections:
        section("Interesting Files")
        text = sections["interesting_files"]
        if "wp-config.php" in text:
            for line in text.split('\n'):
                if "wp-config" in line and line.strip():
                    success(f"WordPress config: {line.strip()}")
        if ".env" in text:
            for line in text.split('\n'):
                if ".env" in line and line.strip() and "===" not in line:
                    warning(f"Environment file: {line.strip()}")
        if "id_rsa" in text or "id_ecdsa" in text or "id_ed25519" in text:
            for line in text.split('\n'):
                if re.search(r'id_(rsa|ecdsa|ed25519)', line) and line.strip():
                    success(f"SSH key: {line.strip()}")
        if "SHADOW_READABLE=yes" in (sections.get("users", "")):
            success("/etc/shadow is readable!")

    # Users
    if "users" in sections:
        section("Users with Shells")
        for line in sections["users"].split('\n'):
            if line.strip() and not line.startswith('===') and 'SHADOW' not in line:
                print(f"  {line.strip()}")

    # Summary
    section("Privesc Summary")
    critical = [f for f in all_findings if f[0] == "CRITICAL"]
    high = [f for f in all_findings if f[0] == "HIGH"]
    unusual = [f for f in all_findings if f[0] == "UNUSUAL"]

    if critical:
        success(f"{len(critical)} CRITICAL vectors found")
        for _, item, desc in critical:
            print(f"    → {desc}: {item}")
    if high:
        warning(f"{len(high)} HIGH-interest items")
    if unusual:
        warning(f"{len(unusual)} unusual items worth investigating")
    if not all_findings:
        warning("No obvious privesc vectors found — manual review recommended")

    data("PRIVESC_CRITICAL", str(len(critical)))
    data("PRIVESC_HIGH", str(len(high)))
    data("PRIVESC_TOTAL", str(len(all_findings)))


def run_via_ghost_listen():
    """Upload and run enum script via ghost-listen daemon."""
    ghost_listen = os.path.join(SCRIPT_DIR, "ghost-listen.py")

    # Check daemon is running
    if not os.path.exists(LISTEN_SOCKET):
        error("ghost-listen daemon not running")
        error("Start it first: python3 tools/ghost-listen.py --lport 4444 &")
        sys.exit(1)

    # Upload enum script
    status("Uploading enumeration script to target...")
    result = subprocess.run(
        [sys.executable, ghost_listen, "--upload", ENUM_SCRIPT, "--dest", "/tmp/ghost-enum.sh"],
        capture_output=True, text=True, timeout=60
    )
    if result.returncode != 0:
        error(f"Upload failed: {result.stderr}")
        sys.exit(1)
    success("Enum script uploaded")

    # Execute and capture output
    status("Running enumeration (this may take a minute)...")
    result = subprocess.run(
        [sys.executable, ghost_listen, "--cmd", "bash /tmp/ghost-enum.sh", "--timeout", "120"],
        capture_output=True, text=True, timeout=180
    )
    if result.returncode != 0:
        error(f"Execution failed: {result.stderr}")
        sys.exit(1)

    # Cleanup
    subprocess.run(
        [sys.executable, ghost_listen, "--cmd", "rm -f /tmp/ghost-enum.sh"],
        capture_output=True, text=True, timeout=15
    )

    return result.stdout


def run_via_ssh(ssh_spec):
    """Run enum script via SSH. Format: user:password@host or user@host."""
    try:
        import paramiko
    except ImportError:
        error("paramiko not installed (pip install paramiko)")
        sys.exit(1)

    # Parse ssh spec
    if ':' in ssh_spec.split('@')[0]:
        user, rest = ssh_spec.split(':', 1)
        password, host = rest.rsplit('@', 1)
    else:
        user, host = ssh_spec.split('@', 1)
        password = None

    port = 22
    if ':' in host:
        host, port = host.rsplit(':', 1)
        port = int(port)

    status(f"Connecting via SSH to {user}@{host}:{port}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        if password:
            client.connect(host, port=port, username=user, password=password, timeout=10)
        else:
            client.connect(host, port=port, username=user, timeout=10)
    except Exception as e:
        error(f"SSH connection failed: {e}")
        sys.exit(1)

    success("SSH connected")

    # Upload script
    status("Uploading enum script...")
    sftp = client.open_sftp()
    sftp.put(ENUM_SCRIPT, "/tmp/ghost-enum.sh")
    sftp.close()

    # Execute
    status("Running enumeration...")
    _, stdout, stderr = client.exec_command("bash /tmp/ghost-enum.sh", timeout=120)
    output = stdout.read().decode("utf-8", errors="replace")

    # Cleanup
    client.exec_command("rm -f /tmp/ghost-enum.sh")
    client.close()

    return output


def main():
    banner("Ghost Enum")

    parser = argparse.ArgumentParser(description="Ghost Enum — Post-exploitation enumeration")
    parser.add_argument("--parse", type=str, default=None,
                        help="Parse saved enum output file")
    parser.add_argument("--ssh", type=str, default=None,
                        help="Run via SSH (user:pass@host or user@host)")
    parser.add_argument("--save", type=str, default=None,
                        help="Save raw output to file")
    args = parser.parse_args()

    # Get raw output
    if args.parse:
        status(f"Parsing saved output: {args.parse}")
        with open(args.parse) as f:
            raw = f.read()
    elif args.ssh:
        raw = run_via_ssh(args.ssh)
    else:
        raw = run_via_ghost_listen()

    # Save if requested
    if args.save:
        os.makedirs(os.path.dirname(args.save) or ".", exist_ok=True)
        with open(args.save, "w") as f:
            f.write(raw)
        success(f"Raw output saved to {args.save}")

    # Parse and analyze
    sections = parse_sections(raw)
    if not sections:
        error("No sections found in output — is the enum script output valid?")
        sys.exit(1)

    data("SECTIONS_FOUND", ",".join(sections.keys()))
    analyze_and_report(sections)


if __name__ == "__main__":
    main()
