# Session: lazyadmin

**Date:** 2026-02-20
**Target IP:** 10.67.162.142
**Room URL:** https://tryhackme.com/room/lazyadmin
**Difficulty:** Easy

---

## Recon

### Nmap Initial Scan
```
22/tcp open  ssh     OpenSSH 7.2p2 Ubuntu 4ubuntu2.8
80/tcp open  http    Apache httpd 2.4.18 (Ubuntu) — default page
```

**Key Findings:**
- Only 2 ports, minimal attack surface
- Apache default page — real app hiding in subdirectory

---

## Enumeration

**Services Investigated:**
- HTTP (80): gobuster found `/content/` → SweetRice 1.5.1 CMS
- SweetRice admin panel at `/content/as/`
- MySQL backup exposed at `/content/inc/mysql_backup/`

**Key Findings:**
- Database backup contains admin credentials in serialized PHP
- Username: `manager`
- Password hash: `42f749ade7f9e195bf475f37a44cafcb` (MD5)
- Cracked: `Password123` (john, rockyou, instant)
- SweetRice 1.5.1 has multiple known vulnerabilities (searchsploit)

---

## Exploitation

**Vector Used:** SweetRice 1.5.1 Arbitrary File Upload (EDB-40716)

**Steps:**
1. Logged into SweetRice admin panel at `/content/as/` with `manager:Password123`
2. Uploaded PHP reverse shell (`shell.php5`) via media center upload
3. Started ghost-listen daemon on port 4444
4. Triggered shell by accessing `/content/attachment/shell.php5`
5. Caught reverse shell as `www-data`

**Result:** Shell as www-data on THM-Chal

---

## Privilege Escalation

**Vector Used:** Sudo misconfiguration + world-writable script

**Steps:**
1. `sudo -l` revealed: `(ALL) NOPASSWD: /usr/bin/perl /home/itguy/backup.pl`
2. `backup.pl` calls `system("sh", "/etc/copy.sh")`
3. `/etc/copy.sh` is world-writable (`-rw-r--rwx`)
4. Overwrote `/etc/copy.sh` with commands to dump root flag
5. Ran `sudo /usr/bin/perl /home/itguy/backup.pl` → executed as root

**Result:** Root access confirmed

---

## Flags

- [x] User flag: `THM{63e5bce9271952aad1113b6f1ac28a07}`
- [x] Root flag: `THM{6637f41d0177b6f37cb20d775124699f}`

---

## Lessons Learned
- SweetRice CMS exposes MySQL backups by default at `/content/inc/mysql_backup/` — always check
- The file upload vuln allows `.php5` extension bypass — common pattern in PHP CMS exploits
- Sudo + script chain: even if you can't modify the sudo target, check what IT calls
- ghost-listen daemon/client pattern worked perfectly for this engagement

## Techniques Used
- Nmap service enumeration
- Directory brute forcing (gobuster)
- Database backup credential extraction
- MD5 hash cracking (john)
- Arbitrary file upload → PHP reverse shell
- sudo -l enumeration
- Writable script exploitation

## Areas to Improve
- ghost-recon.sh should fall back to `-Pn` if host appears down
- Could write a SweetRice exploit module for ghost-exploit.py
