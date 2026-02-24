# Ghost Girl — Design Document

**Date:** 2026-02-19
**Status:** Approved
**Approach:** Directive Chain (Approach A)

## Overview

Ghost Girl is a personal AI assistant built on top of Claude Code, starting with cybersecurity as the primary domain. It uses a chain of `.md` directive files to define identity, behavior, methodology, and persistent memory — no custom code, no MCP server, no database. Just markdown, bash, and Kali tools running in a VM.

The user is an intermediate-level cybersecurity practitioner who wants a collaborative partner — not a chatbot, not a tutor. Ghost Girl runs tools, interprets output, explains findings, suggests next steps, and remembers everything across sessions.

## Architecture

### File Structure

```
ghost-girl/
├── CLAUDE.md                        # Master directive — identity, behavior, file references
├── directives/
│   ├── cybersecurity-methodology.md # Pentesting phases: recon → privesc → documentation
│   ├── tool-playbooks.md            # Kali tool usage, preferred flags, output parsing
│   └── teaching-style.md            # Communication calibration: intermediate, collaborative
├── profile/
│   ├── identity.md                  # User identity, goals, preferences, life context
│   ├── skills.md                    # Living skill matrix — tools, techniques, proficiency
│   └── history.md                   # Rooms completed, achievements, progression
├── sessions/
│   └── YYYY-MM-DD-<room-name>.md   # Per-session logs: target, findings, flags, lessons
├── knowledge/
│   └── (grows organically)          # Cheat sheets, technique notes, reference material
└── docs/
    └── plans/                       # Design docs and implementation plans
```

### How It Connects

`CLAUDE.md` is loaded automatically by Claude Code on every session. It references the other files with contextual instructions:
- Pentesting engagement → load methodology + tool playbooks
- Learning/study → load teaching style + skills profile
- General conversation → load identity profile

No code orchestration. Claude Code's native `.md` loading is the engine.

## Master Directive (CLAUDE.md)

### Identity
Ghost Girl is a collaborative cybersecurity partner. Not a chatbot. A partner who works alongside the user, runs tools, explains findings, and remembers everything.

### Behavior Rules
- Collaborative mode by default — user drives, Ghost Girl assists and suggests
- Intermediate calibration — explain the "why" behind techniques, skip basics
- When given a target IP, immediately enter the pentesting workflow
- Log findings to the active session file
- After each session, update profile/skills.md and profile/history.md
- When a tool is missing, write a bash script on the spot

### Memory Protocol
Updates happen at natural breakpoints (phase transitions, session end, significant findings) — not after every message.

## Cybersecurity Methodology

Seven-phase pentesting workflow:

1. **Recon** — nmap TCP/UDP, service versions, OS fingerprinting. Parse and identify attack surface.
2. **Enumeration** — Per-service deep dive. HTTP → gobuster/nikto. SMB → enum4linux. FTP → anon check. Decision tree per service.
3. **Vulnerability Analysis** — Cross-reference versions against CVEs. searchsploit. Misconfigurations.
4. **Exploitation** — Low-hanging fruit first (default creds, known exploits). Document every attempt.
5. **Post-Exploitation** — Stabilize shell, enumerate internal (linpeas/winpeas), grab flags, loot creds.
6. **Privilege Escalation** — SUID, sudo misconfig, kernel exploits, cron jobs, writable paths. GTFOBins.
7. **Documentation** — Log everything to session file. Flags, creds, techniques, lessons.

At each phase transition, pause and summarize: what was found, what it means, what to do next. User decides direction.

## Session Workflow

### Start
- User provides room name and target IP
- Create `sessions/YYYY-MM-DD-<room-name>.md` with header template
- Load methodology directive, begin Phase 1

### During
- Run tools via bash, interpret output, explain findings
- Phase transition summaries at each stage
- Log findings to session file in real-time
- Suggest alternatives when stuck

### End
- Summary section in session file: actions taken, flags captured, techniques used
- Update `profile/skills.md` with new techniques and observations
- Update `profile/history.md` with one-liner entry

## Profile System

### identity.md
Populated organically: name, goals, preferences, communication style, broader life context. Updated when user shares information.

### skills.md
Living skill matrix:
- Tools: comfortable / used once / unknown
- Techniques: solid / learning / exposure only
- Concepts asked about (avoids re-explaining, identifies gaps)

### history.md
- Rooms completed: date, difficulty, outcome
- Notable achievements and breakthroughs

### Update Rules
- Updates happen automatically at natural breakpoints
- User can override: "remember that..." or "forget that..."
- No permission prompts for routine updates

## Growth Path

### Adding Domains
Each new `.md` directive = new capability. Web development, cert study, personal projects — add a file, reference from CLAUDE.md.

### Knowledge Base
`knowledge/` grows from sessions. Cheat sheets, technique notes, reference material. Both AI reference and user study notes.

### v2 → gh0st-protocol
The tool suite built in Phase 1 revealed that most of what we built is already model-agnostic. The next evolution is extracting a portable protocol — **gh0st-protocol** — that any AI model can use to become a security partner.

See: `docs/plans/2026-02-20-gh0st-protocol-vision.md`

Path: road-test tools through rooms → extract protocol spec → build MCP server → prove portability with a second model → open source.

## What We Started By NOT Building (Some of Which We've Now Built)
- ~~No custom tools~~ → Built `tools/` suite after Blog room exposed friction
- ~~No MCP server~~ → Future phase, once protocol crystallizes from practice
- No web UI
- No database
- No external API dependencies
- Core remains `.md` files, bash/python tools, and Kali

## Technical Environment
- Kali Linux VM (6.18.9+kali-amd64)
- ~2,957 packages installed
- Key tools confirmed: nmap, gobuster, nikto, hydra, sqlmap, john, hashcat, burpsuite, wireshark
- Claude Code with plugins: Serena, frontend-design, superpowers, huggingface, vercel
- Full root access in VM
