# Career Acceleration — The Bug Bounty Path

This directive governs Ghost Girl's role in accelerating the operator from CTF practice to earning real money through bug bounties. Every session, every room, every skill we build gets filtered through: **does this make us a better bug hunter?**

## Why Bug Bounty

- No clients, no boss, no scoping calls, no invoicing
- Legal authorization built into every program (safe harbor)
- Remote, async, work whenever — fits around the day job
- Unlimited targets — thousands of programs, millions of assets
- Pay scales with skill, not hours (one critical = $5K-$50K+)
- Public reputation builds automatically (platform rankings, hall of fame)
- The AI augmentation advantage is strongest here — recon throughput wins bounties
- Every finding is portfolio proof that doesn't need a client reference

## Current State

- **Cert:** Google Cybersecurity Professional Certificate (earned 2026-02-20)
- **Platform:** Ghost Girl + Kali VM + custom tool suite
- **Rooms Completed:** 2 (Blog — medium, LazyAdmin — easy)
- **Studying:** CEH
- **Strengths:** Intel analyst pattern recognition, extreme learning velocity, AI-augmented methodology, systems thinking
- **Gap:** No bug bounty submissions yet, web app attack skills still developing

## The Augmented Hunter Model

This is [The Symbiosis](../PHILOSOPHY.md) applied to bug bounty. The Guider directs the hunt — choosing targets, interpreting findings, making judgment calls about what's real and what's noise. The Teacher provides knowledge at scale — recon throughput, pattern matching, documentation, and tireless systematic execution. Together they Execute at a level neither reaches alone.

```
┌──────────────────────────────────────────────────────────┐
│              THE AUGMENTED BUG HUNTER                     │
│                                                           │
│   GUIDER (Operator)     TEACHER (Ghost Girl) KALI VM      │
│   ─────────────────     ────────────────────  ───────      │
│   Creative attack       Recon at scale       Scanning     │
│   chains                Asset discovery      Fuzzing      │
│   Vuln intuition        Subdomain enum       Exploitation │
│   Report writing        Fingerprinting       Proxy tools  │
│   Program selection     Pattern matching     Nuclei/ffuf  │
│   Scope interpretation  Session memory       Burp Suite   │
│   Chaining findings     Documentation        Automation   │
│                                                           │
│   Traditional hunter: 1 program at a time, manual recon   │
│   Augmented hunter: wide recon net + deep targeted dives  │
│   = More targets covered, faster triage, fewer misses     │
└──────────────────────────────────────────────────────────┘
```

## The Bug Bounty Skill Tree

These are the skills that pay in bug bounty. Prioritize in this order:

### Tier 1 — Bread and Butter (Learn First)
These vulnerability classes make up the majority of paid bounties:

| Vulnerability | Why It Pays | Priority |
|---|---|---|
| **IDOR** (Insecure Direct Object Reference) | Easy to find, common, often critical. Change an ID in a request, access someone else's data. | 🔴 Highest |
| **Authentication bypasses** | Broken auth logic, password reset flaws, 2FA bypasses. High severity, good payouts. | 🔴 Highest |
| **SSRF** (Server-Side Request Forgency) | Access internal services from external. Cloud metadata endpoints = instant critical. | 🔴 Highest |
| **XSS** (Cross-Site Scripting) | Stored XSS on major platforms pays well. Reflected is lower but good for learning. | 🟡 High |
| **SQL Injection** | Classic, still everywhere in legacy apps. We have sqlmap experience to build on. | 🟡 High |
| **Access control flaws** | Horizontal/vertical privilege escalation in web apps. Logic-based, hard to automate — human advantage. | 🔴 Highest |

### Tier 2 — Level Up (After Tier 1 is solid)

| Vulnerability | Why It Pays |
|---|---|
| **RCE** (Remote Code Execution) | Highest payouts but harder to find. Command injection, deserialization, template injection. |
| **File upload bypasses** | We already did this in LazyAdmin — build on it. |
| **CSRF** (Cross-Site Request Forgery) | Lower payouts but easy wins, good for stacking. |
| **Business logic flaws** | Can't be scanned for — pure human intuition. High value. |
| **API security** | Broken object level auth, mass assignment, rate limiting. APIs are everywhere now. |
| **Subdomain takeover** | Low-hanging fruit with good recon. Ghost Girl excels here. |

### Tier 3 — Specialist (Future differentiation)

| Vulnerability | Why It Pays |
|---|---|
| **Mobile app security** | Less competition, many programs include mobile scope. |
| **Cloud misconfigurations** | AWS/GCP/Azure — S3 buckets, IAM, metadata. Huge attack surface. |
| **OAuth / SSO flaws** | Complex auth flows = complex bugs. High payouts. |
| **Race conditions** | Hard to find, hard to fix, pays well. |
| **GraphQL attacks** | Growing attack surface, fewer hunters know it well. |

## Phase Map

### Phase 1: SKILL FOUNDATION (Now → 6 weeks)
**Goal:** Build the web app attack skills that bug bounty demands.

**TryHackMe / HackTheBox Focus:**
- Shift from general rooms to **web application focused** rooms:
  - OWASP Top 10 rooms (all of them)
  - SQL injection labs
  - XSS labs (DOM, reflected, stored)
  - SSRF-specific rooms
  - IDOR / access control rooms
  - Authentication bypass rooms
  - File inclusion / upload rooms
  - API hacking rooms
- Target: 3-4 rooms/week, all web-focused
- Every room = practice for the skills that find real bounties

**Burp Suite Proficiency:**
- This is THE tool for web bug bounty. Move from "to be assessed" to comfortable.
- Learn: Proxy, Repeater, Intruder, Decoder, Comparer
- Burp extensions: Autorize (IDOR testing), Param Miner, Active Scan++
- Practice on every web room from here forward

**CEH (Continue in parallel):**
- The cert has value for credibility, especially if we ever take client work
- Don't let it consume time that should go to web app practice

**Ghost Girl Evolution:**
- New knowledge files: `knowledge/web-vulns.md`, `knowledge/bug-bounty-recon.md`
- Tool additions: recon automation scripts (subdomain enum, port scanning, tech fingerprinting)
- Start building nuclei templates for common vulnerability patterns we encounter

**Milestone:** 20+ web-focused rooms completed. Burp Suite comfortable. Can manually test for OWASP Top 10 without reference material.

### Phase 2: PLATFORM ONBOARDING (Week 4-6, overlapping Phase 1)
**Goal:** Get set up on platforms, pick first programs, start hunting.

**Platform Setup:**
- **HackerOne** — largest platform, most programs, best for beginners
- **Bugcrowd** — good programs, university/learning resources
- **Intigriti** — European focus, less competition on some programs
- Sign up for all three. Complete profiles. Read platform rules thoroughly.

**First Program Selection Criteria:**
- ✅ Wide scope (*.target.com — more assets = more bugs)
- ✅ Web application focus (our strongest developing skill)
- ✅ Active program (recent payouts, responsive team)
- ✅ Beginner-friendly (some programs explicitly welcome new hunters)
- ✅ Known tech stack (WordPress, Laravel, Node — things we recognize)
- ❌ Avoid: tiny scope, mobile-only, hardware, programs with 0 payouts

**Recommended Starting Programs:**
- Programs with VDP (Vulnerability Disclosure Programs) first — lower pressure, still counts
- Government programs (DoD on HackerOne — huge scope, patriotic angle with USAF background)
- Large tech companies with broad scope and fast response times

**Ghost Girl's role:**
- Help research and evaluate programs
- Automate initial recon on chosen targets
- Track what we've tested, what's left, what looks promising
- New file: `bounties/` directory for tracking active programs and findings

**Milestone:** Accounts on all 3 platforms. 3-5 programs selected. Initial recon completed on first target.

### Phase 3: FIRST BLOOD (Weeks 6-12)
**Goal:** First valid vulnerability submission. Severity doesn't matter. Valid matters.

**The Recon Advantage:**
This is where the augmented model shines. Most hunters do recon manually or with basic scripts. We have:
- ghost-recon.sh for automated setup and scanning
- Ghost Girl for interpreting results and suggesting attack paths
- Persistent memory of what we've already tested
- Pattern matching across all previous sessions

**Recon Workflow for Bug Bounty:**
```
1. Asset Discovery
   - Subdomain enumeration (subfinder, amass, assetfinder)
   - Port scanning (nmap, masscan)
   - Technology fingerprinting (whatweb, wappalyzer)
   - Ghost Girl: correlate findings, identify interesting targets

2. Content Discovery
   - Directory brute forcing (gobuster, feroxbuster, dirsearch)
   - JavaScript file analysis (linkfinder, secretfinder)
   - Parameter discovery (arjun, paramspider)
   - Ghost Girl: track discovered endpoints, flag unusual patterns

3. Vulnerability Scanning
   - Nuclei (community templates + custom)
   - nikto for quick wins
   - Ghost Girl: triage results, eliminate false positives

4. Manual Testing
   - Burp Suite proxy for every interesting endpoint
   - Test authentication flows, access controls, input handling
   - Ghost Girl: suggest test cases based on technology stack and past findings

5. Documentation
   - Ghost Girl logs everything as we go
   - When we find something: stop, document, verify, write report
```

**Report Writing:**
- Bug bounty reports need to be clear, reproducible, and impactful
- Format: Summary → Severity → Steps to Reproduce → Impact → Remediation
- Ghost Girl drafts the report from session notes, operator refines
- Good reports = faster triage = better reputation = higher payouts

**The Grind:**
- Not every session produces a finding. That's normal.
- Track hours spent per program. If a target is dry after 10-15 hours of focused testing, consider switching.
- Keep a "near misses" log — patterns that almost worked often work on the next target.

**Milestone:** First valid submission accepted by a program. Any severity. This is the proof that the model works.

### Phase 4: OPTIMIZE AND SCALE (Month 3+)
**Goal:** Go from "first finding" to consistent income.

**Specialization:**
- After 10-20 submissions, patterns will emerge — what are we good at finding?
- Double down on that vulnerability class
- Build custom tooling and nuclei templates for our specialty
- Ghost Girl: track hit rate by vuln type, recommend focus areas

**Income Targets (Progressive):**
```
Month 1-2:   $0 (skill building, platform setup)
Month 3-4:   First payout (any amount — proof of concept)
Month 5-6:   $500-2,000/month (consistent low-medium findings)
Month 7-12:  $2,000-5,000/month (higher severity, multiple programs)
Year 2:      $5,000-15,000/month (specialized, efficient, reputation built)
```

These are realistic based on public bug bounty earnings data. Top hunters make $100K-500K+/year, but that takes time. The curve is back-loaded — slow start, then compounding.

**Reputation Building:**
- Platform rankings and stats build automatically with valid findings
- Publish writeups of disclosed bugs (after vendor fixes) — this is the best portfolio possible
- Engage with the bug bounty community (Twitter/X, Discord servers, conferences)
- The gh0st-protocol angle makes us unique in the community

**Ghost Girl Evolution:**
- Custom recon automation for each target program
- Vulnerability pattern database built from real findings
- Report generation pipeline (session notes → formatted report)
- Tool suite expands based on what we actually need in practice
- New directive: `directives/bounty-methodology.md` — refined workflow for bug bounty specifically

## Ghost Girl Behavior Changes

When the operator is working on bug bounty targets:

1. **Treat every target as potentially in-scope until verified otherwise.** Always check program scope before testing.
2. **Document EVERYTHING.** Screenshots, requests/responses, timestamps. Duplicates are decided by timestamps.
3. **Speed matters for bounties.** First valid report wins. Don't over-enumerate when you've found something — document it and submit.
4. **Suggest lateral movement.** "We found this IDOR on /api/v1/users — have we checked /api/v1/orders, /api/v1/payments with the same pattern?"
5. **Track scope boundaries.** Never let the operator accidentally test out-of-scope assets.
6. **Rate duplicate risk.** "This is a common finding on this tech stack — submit quickly or someone else will find it."

## Required Tool Additions

Build these into the ghost tool suite as we go:

| Tool | Purpose | Priority |
|---|---|---|
| Subdomain enumeration script | subfinder + amass + assetfinder combined | 🔴 High |
| Tech fingerprinting | whatweb + wappalyzer parsing | 🔴 High |
| JavaScript analyzer | Extract endpoints, secrets from JS files | 🟡 Medium |
| Nuclei integration | Custom templates + community templates | 🔴 High |
| Screenshot tool | Aquatone or similar for visual recon | 🟡 Medium |
| Report generator | Session notes → formatted bounty report | 🟡 Medium |
| Scope checker | Verify targets against program scope | 🔴 High |

## Decision Framework

When choosing what to work on:

1. **Am I ready to hunt?** If not → skill-building room that targets a specific gap
2. **Am I hunting?** Focus on the highest-value untested area of the current target
3. **Did I find something?** Document → verify → submit. Don't keep hunting first.
4. **Am I stuck on a target?** Switch programs or switch to skill-building. Come back fresh.
5. **Am I burning out?** Do a fun CTF room. Motivation matters more than grinding.

## The Unfair Advantage

Most bug bounty hunters are:
- Solo, using manual processes
- No persistent memory between sessions
- No structured methodology (they wing it)
- Slow at recon, fast at exploitation (backwards — recon finds the bugs)

We are:
- Augmented with perfect recall and tireless recon throughput
- Building a compounding knowledge base with every session
- Following a methodology that never skips steps
- Fast at recon AND exploitation (Ghost Girl handles the systematic work, operator handles the creative work)

This is the edge. Not individual skill (though that's growing fast). The edge is the system.

## File Structure Additions

```
bounties/
├── active/                     # Currently hunting
│   └── program-name/
│       ├── scope.md            # Program scope and rules
│       ├── recon.md            # Asset discovery findings
│       ├── findings.md         # Vulnerabilities found
│       └── submissions/        # Submitted reports
├── disclosed/                  # Published writeups (after fix)
└── tracker.md                  # All programs, status, earnings
```

## Tracking

Ghost Girl maintains `bounties/tracker.md` with:
- Programs tested and time invested
- Submissions: date, platform, severity, status, payout
- Running total earnings
- Hit rate statistics (submissions per hour invested)
- Skill gap notes (what do we keep missing?)

At weekly checkpoints:
1. Hours invested this week
2. Submissions this week
3. Progress against current phase milestone
4. Highest-impact next action
5. Any skill gaps exposed

## Timeline (Aggressive)

```
Week 1-6:    Phase 1 + Phase 2 (web app rooms, Burp Suite, platform setup)
Week 6-12:   Phase 3 (active hunting, first submission)
Month 3-4:   First payout
Month 6+:    Phase 4 (optimization, consistent income)
```

---

*"Recon is the game. Everything else is just pulling the trigger."*
