# Operator Skills

## Tools

| Tool | Proficiency | Notes |
|---|---|---|
| nmap | Comfortable | Understands -sC/-sV, reads output well |
| wpscan | Comfortable | Used xmlrpc brute force, user enumeration |
| gobuster | (to be assessed) | |
| nikto | (to be assessed) | |
| hydra | (to be assessed) | |
| sqlmap | (to be assessed) | |
| john | Comfortable | MD5 cracking with rockyou, fast and effective |
| hashcat | (to be assessed) | |
| burpsuite | (to be assessed) | |
| metasploit | Comfortable | Ran wp_crop_rce, handled meterpreter to shell transition |
| wireshark | (to be assessed) | |
| smbclient | Comfortable | Anonymous share enumeration |
| ltrace | Introduced | Used for SUID binary analysis on Blog room |

## Techniques

| Technique | Proficiency | Notes |
|---|---|---|
| Network scanning | Comfortable | Solid nmap workflow |
| Web enumeration | Comfortable | WPScan, WordPress-specific enum |
| SMB enumeration | Comfortable | Anonymous access, enum4linux |
| SQL injection | (to be assessed) | |
| Reverse shells | Comfortable | Meterpreter + shell stabilization |
| Linux privesc | Learning | SUID binary (Blog), sudo script chain (LazyAdmin) — building pattern recognition |
| Windows privesc | (to be assessed) | |
| Password cracking | Comfortable | MD5 cracking with john, credential extraction from DB backups |
| Buffer overflow | (to be assessed) | |

## Concepts Asked About
- Custom SUID binary analysis (ltrace)
- Environment variable manipulation for privilege escalation

## Areas to Focus On
- More privesc practice — the SUID/ltrace path was new
- Manual exploitation (less reliance on Metasploit over time)
