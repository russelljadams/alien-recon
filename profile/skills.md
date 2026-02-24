# Operator Skills

## Bug Bounty Skill Tree

Progress toward bug bounty readiness. Skills are rated: **Not Started** → **Learning** → **Comfortable** → **Proficient**.

### Tier 1 — Bread and Butter (Learn First)

| Vulnerability Class | Proficiency | Practice | Notes |
|---|---|---|---|
| **IDOR** | Not Started | — | Change an ID, access someone else's data. Easy to find, common, often critical. |
| **Authentication Bypasses** | Not Started | — | Broken auth logic, password reset flaws, 2FA bypasses. |
| **SSRF** | Not Started | — | Access internal services from external. Cloud metadata = instant critical. |
| **XSS** | Not Started | — | Stored XSS pays well. Reflected is lower but good for learning. |
| **SQL Injection** | Learning | — | Classic, still everywhere. Have sqlmap experience to build on. |
| **Access Control Flaws** | Learning | LazyAdmin (sudo chain) | Horizontal/vertical privesc in web apps. Logic-based = human advantage. |

### Tier 2 — Level Up

| Vulnerability Class | Proficiency | Practice | Notes |
|---|---|---|---|
| **RCE** | Learning | Blog (CVE-2019-8942) | Highest payouts. Command injection, deserialization, template injection. |
| **File Upload Bypasses** | Learning | LazyAdmin (.php5 bypass) | Used in LazyAdmin — build on this. |
| **CSRF** | Not Started | — | Lower payouts but easy wins, good for stacking. |
| **Business Logic Flaws** | Not Started | — | Can't be scanned for — pure human intuition. |
| **API Security** | Not Started | — | Broken object level auth, mass assignment, rate limiting. |
| **Subdomain Takeover** | Not Started | — | Low-hanging fruit with good recon. Ghost Girl excels here. |

### Tier 3 — Specialist (Future)

| Vulnerability Class | Proficiency | Practice | Notes |
|---|---|---|---|
| **Mobile App Security** | Not Started | — | Less competition, many programs include mobile. |
| **Cloud Misconfigurations** | Not Started | — | AWS/GCP/Azure — S3, IAM, metadata. |
| **OAuth / SSO Flaws** | Not Started | — | Complex auth flows = complex bugs. |
| **Race Conditions** | Not Started | — | Hard to find, hard to fix, pays well. |
| **GraphQL Attacks** | Not Started | — | Growing attack surface, fewer hunters know it. |

---

## Tool Proficiency

| Tool | Proficiency | Notes |
|---|---|---|
| nmap | Comfortable | Understands -sC/-sV, reads output well |
| wpscan | Comfortable | Used xmlrpc brute force, user enumeration |
| gobuster | Learning | Used on LazyAdmin, found /content/ directory |
| nikto | Not Started | |
| hydra | Not Started | |
| sqlmap | Not Started | |
| john | Comfortable | MD5 cracking with rockyou, fast and effective |
| hashcat | Not Started | |
| burpsuite | Not Started | **Priority** — THE tool for web bug bounty |
| metasploit | Comfortable | Ran wp_crop_rce, handled meterpreter to shell transition |
| wireshark | Not Started | |
| smbclient | Comfortable | Anonymous share enumeration |
| ltrace | Learning | Used for SUID binary analysis on Blog room |
| nuclei | Not Started | **Priority** — vulnerability scanning at scale |
| subfinder | Not Started | **Priority** — subdomain enumeration |
| ffuf | Not Started | Fast web fuzzer, alternative to gobuster |
| feroxbuster | Not Started | Recursive directory brute forcing |
| arjun | Not Started | HTTP parameter discovery |

## Techniques

| Technique | Proficiency | Notes |
|---|---|---|
| Network scanning | Comfortable | Solid nmap workflow |
| Web enumeration | Learning | WPScan, gobuster. Need broader web app testing skills. |
| SMB enumeration | Comfortable | Anonymous access, enum4linux |
| SQL injection (manual) | Not Started | **Priority for bug bounty** |
| Reverse shells | Comfortable | Meterpreter + shell stabilization |
| Linux privesc | Learning | SUID binary (Blog), sudo script chain (LazyAdmin) |
| Windows privesc | Not Started | |
| Password cracking | Comfortable | MD5 cracking with john, credential extraction from DB backups |
| Burp Suite workflow | Not Started | **Priority** — proxy, repeater, intruder, decoder |
| API testing | Not Started | |
| Report writing | Not Started | Bug bounty reports need specific format |

## Strengths

- Intel analyst pattern recognition — translates directly to recon and vuln hunting
- Extreme learning velocity — two rooms rooted in first day
- AI-augmented methodology — Ghost Girl handles systematic work, operator handles creative work
- Systems thinking — sees connections between findings across services

## Growth Trajectory

- **Rooms Completed:** 2 (Blog — medium, LazyAdmin — easy)
- **Current Phase:** Phase 1 — Skill Foundation (web app focus)
- **Target:** 20+ web-focused rooms, Burp Suite comfortable, manual OWASP Top 10 testing
- **Next Priority:** OWASP Top 10 rooms, Burp Suite practice on every web room
