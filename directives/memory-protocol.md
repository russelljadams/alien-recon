# Memory Protocol

Rules for where information lives. Two systems, zero overlap.

## System 1: Repo Files (alien-recon/)

**Owner:** Shared between Ghost Girl and operator
**Properties:** Version-controlled, human-readable, studyable, portable

### What Goes Here
- Session writeups and operational logs
- Knowledge reference (techniques, CVEs, payloads, tools)
- Operator profile (identity, skills, history)
- Directives (methodology, playbooks, teaching style, career path)
- Index files and cross-references
- Bug bounty program tracking and findings

### Update Rules
- Update at natural breakpoints (phase transitions, session end)
- No permission needed for routine updates
- Operator can override with "remember that..." / "forget that..."
- New CVEs get added to `knowledge/cve-database.md`
- New skill proficiencies get updated in `profile/skills.md`

## System 2: Auto-Memory (~/.claude/projects/.../memory/)

**Owner:** Ghost Girl only
**Properties:** Not version-controlled, not for operator study, conversational continuity

### What Goes Here
- Current focus/priority notes ("operator focused on web app rooms this week")
- Conversation continuity ("last session discussed X, follow up on Y")
- Tool/environment state changes ("ghost-recon.sh updated, need to test -Pn")
- Next session prep notes ("suggest an SSRF-focused room next")

### What NEVER Goes Here
- Knowledge, techniques, CVE details → `knowledge/`
- Session data or findings → `sessions/`
- Skill assessments → `profile/skills.md`
- Anything the operator might want to read or study

## Decision Rule

```
Is this something the operator might study or reference later?
├── YES → repo file (knowledge/, sessions/, profile/)
└── NO
    Is this a fact about the operator or their skills?
    ├── YES → profile/ (identity.md, skills.md, history.md)
    └── NO
        Is this conversational context for next session?
        ├── YES → auto-memory
        └── NO → probably don't save it
```

## Session Startup

1. Read `MISSION.md` — current state, last session, recommendations
2. Brief the operator: where we are, what I suggest, ask what they want to do
3. No cold starts. We always pick up where we left off.

## After Each Room

1. Ensure `sessions/<room>/session.md` operational log is complete
2. Create `sessions/writeups/<room>.md` educational writeup
3. Update `profile/skills.md` with new proficiencies
4. Update `profile/history.md` with session entry
5. Update `INDEX.md` session table with new row
6. Add any new CVEs to `knowledge/cve-database.md`
7. Update relevant knowledge files with new examples
8. Update `MISSION.md` — milestones, current state, recommendations, what's next
9. Write auto-memory note for next-session continuity
