# Session: Blog

**Date:** 2026-02-20
**Target IP:** 10.67.177.160
**Room URL:** https://tryhackme.com/room/blog
**Difficulty:** Medium

---

## Recon

### Nmap Initial Scan
4 open ports:
| Port | Service | Version |
|------|---------|---------|
| 22 | SSH | OpenSSH 7.6p1 Ubuntu |
| 80 | HTTP | Apache 2.4.29 / WordPress 5.0 |
| 139 | SMB | Samba 3.X-4.X |
| 445 | SMB | Samba 4.7.6-Ubuntu |

Full port scan confirmed no additional ports.

**Key Findings:**
- WordPress 5.0 (insecure, known RCE via CVE-2019-8942)
- robots.txt disallows /wp-admin/
- SMB with anonymous access

---

## Enumeration

**Services Investigated:**

### WordPress (WPScan)
- Version: 5.0
- Theme: Twenty Twenty 1.3
- Users: `kwheel` (Karen Wheeler), `bjoel` (Billy Joel)
- XML-RPC enabled
- Upload directory listing enabled
- No vulnerable plugins found

### SMB
- `BillySMB` share accessible anonymously
- Contents: Alice-White-Rabbit.jpg, tswift.mp4, check-this.png
- All rabbit holes — no useful data

### enum4linux (RID cycling)
- `bjoel` (UID 1000) — real system user
- `smb` (UID 1001) — service account

### Brute Force
- WPScan xmlrpc password attack against kwheel and bjoel
- **Result:** `kwheel:cutiepie1`

---

## Exploitation

**Vector Used:** WordPress 5.0 Crop-Image RCE (CVE-2019-8942)

**Steps:**
1. Used Metasploit `exploit/multi/http/wp_crop_rce`
2. Authenticated as `kwheel:cutiepie1`
3. Exploit uploaded malicious image, used crop-image path traversal to write PHP shell into theme
4. Reverse shell callback to attacker on port 4444

**Result:** Meterpreter session as `www-data`

---

## Post-Exploitation

- `www-data` — no sudo access
- `/home/bjoel/user.txt` is a troll: "You won't find what you're looking for here. TRY HARDER"
- DB creds from wp-config.php: `wordpressuser:LittleYellowLamp90!@` (database: blog)
- SUID binary found: `/usr/sbin/checker` — custom, non-standard

---

## Privilege Escalation

**Vector Used:** Custom SUID binary `/usr/sbin/checker`

**Analysis with ltrace:**
```
getenv("admin") = nil
puts("Not an Admin")
```

Binary checks for existence of `admin` environment variable. No value validation.

**Steps:**
1. `export admin=1`
2. `/usr/sbin/checker`
3. Dropped to root shell

**Result:** root access

---

## Flags

- [x] Root flag: `9a0b2b618bef9bfa7ac28c1353d9f318`
- [x] User flag: `c8421899aae571f7af486492b71a8ab7` (found in `/media/usb/`, only readable as root)

---

## Answers
- CMS: WordPress
- CMS Version: 5.0

---

## Lessons Learned
- SMB shares can be rabbit holes — check but don't waste time on stego without reason
- Always check for custom SUID binaries — they stand out from stock OS binaries
- `ltrace` is essential for understanding unknown SUID binaries
- User flags aren't always in /home/<user>/ — search the whole filesystem
- WordPress 5.0 crop-image RCE only needs Author-level creds (not admin)

## Techniques Used
- Nmap service/version scanning
- WPScan user enumeration + xmlrpc brute force
- SMB anonymous enumeration (smbclient, enum4linux)
- Metasploit wp_crop_rce exploit
- SUID binary discovery + ltrace analysis
- Environment variable manipulation for privesc

## Areas to Improve
- (to be assessed after session debrief)
