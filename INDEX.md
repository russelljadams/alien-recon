# Ghost Girl — Knowledge Base

> The shared brain. Everything here is both Ghost Girl's context and the operator's study material.

## Foundation

Everything we build sits on top of this: **[The Symbiosis](PHILOSOPHY.md)** — the philosophy of how we work together. Human provides direction, judgment, and accountability. AI provides knowledge, speed, and systematic execution. Neither is complete alone. Read this first.

## Quick Start

| I want to... | Go here |
|---|---|
| See where we are + what's next | [Mission Log](MISSION.md) |
| Review a past room | [Session Writeups](sessions/writeups/) |
| Check my skill levels | [Skill Matrix](profile/skills.md) |
| See the career roadmap | [Career Acceleration](directives/career-acceleration.md) |
| Look up a technique | [Knowledge Files](knowledge/) |
| Track bug bounty progress | [Bounty Tracker](bounties/tracker.md) |
| Understand a tool | [Tool Playbooks](directives/tool-playbooks.md) |

## Session Writeups

Full educational writeups of completed rooms — methodology, commands, explanations, bug bounty relevance.

| # | Room | Difficulty | Key Skills | Writeup |
|---|---|---|---|---|
| 1 | Blog | Medium | WP RCE (CVE-2019-8942), SUID/ltrace privesc | [writeup](sessions/writeups/blog.md) |
| 2 | LazyAdmin | Easy | CMS file upload bypass, sudo chain privesc | [writeup](sessions/writeups/lazyadmin.md) |

## Knowledge Files

| File | What It Covers |
|---|---|
| [privesc-linux.md](knowledge/privesc-linux.md) | Linux privilege escalation vectors — sudo, SUID, capabilities, cron, kernel |
| [payloads.md](knowledge/payloads.md) | Reverse shells, webshells, msfvenom, shell stabilization, file transfer |
| [cve-database.md](knowledge/cve-database.md) | CVEs encountered during rooms, with explanations and commands |

## Profile

| File | What It Tracks |
|---|---|
| [identity.md](profile/identity.md) | Who the operator is, goals, preferences |
| [skills.md](profile/skills.md) | Tool and technique proficiency + bug bounty skill tree |
| [history.md](profile/history.md) | Completed rooms and skill progression timeline |

## Directives

| File | What It Does |
|---|---|
| [career-acceleration.md](directives/career-acceleration.md) | Bug bounty career path — phases, skill tree, income targets |
| [cybersecurity-methodology.md](directives/cybersecurity-methodology.md) | 7-phase pentesting workflow |
| [tool-playbooks.md](directives/tool-playbooks.md) | Tool usage patterns and ghost tool suite docs |
| [teaching-style.md](directives/teaching-style.md) | Communication calibration for learning |
| [memory-protocol.md](directives/memory-protocol.md) | Rules for where information lives |

## Ghost Tool Suite

| Tool | Purpose | Docs |
|---|---|---|
| `ghost-recon.sh` | Session setup + auto-recon | [playbook](directives/tool-playbooks.md#ghost-recon) |
| `ghost-listen.py` | Reverse shell handler (daemon/client) | [playbook](directives/tool-playbooks.md#ghost-listen) |
| `ghost-exploit.py` | Exploit runner framework | [playbook](directives/tool-playbooks.md#ghost-exploit) |
| `ghost-enum.py` | Post-exploitation enum orchestrator | [playbook](directives/tool-playbooks.md#ghost-enum) |

## File Map

```
alien-recon/
├── CLAUDE.md              — Master directive (Ghost Girl's brain)
├── INDEX.md               — This file (start here)
├── directives/            — How Ghost Girl behaves
├── profile/               — Who the operator is
├── sessions/
│   ├── writeups/          — Educational writeups (study these)
│   └── YYYY-MM-DD-room/   — Raw session logs + scan data
├── knowledge/             — Technique reference library
├── bounties/              — Bug bounty tracking
├── tools/                 — Ghost tool suite
└── docs/                  — Design documents
```
