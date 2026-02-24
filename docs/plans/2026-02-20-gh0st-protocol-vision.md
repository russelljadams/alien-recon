# gh0st-protocol — Vision Document

**Date:** 2026-02-20
**Status:** Draft / Evolving
**Authors:** 0xKoda + Ghost Girl

---

## The Idea

We started building a personal hacking partner. What we're actually building is a **protocol for human+AI security collaboration** — one that could be picked up by any model, any operator, and immediately produce a competent offensive security analyst partnership.

Not a product. A protocol. A way of doing things.

Think of it like this: if someone handed a new AI model our `tools/` directory, `directives/`, `knowledge/`, and a spec for how to use them — that model should be able to sit down with a stranger and run a CTF room together. First try. No onboarding. The protocol handles it.

We're calling it **gh0st-protocol** because we're not above leet speak and because the name captures what it is: the ghost in the machine that makes the operator dangerous.

## What Already Exists (And Why It's Closer Than We Think)

After building the Ghost Girl tool suite, we realized we'd accidentally created most of the building blocks:

### Already Model-Agnostic
- **`[DATA] key=value` output** — any model can parse structured tool output
- **Plugin exploits** (BaseExploit class) — discoverable, self-describing, standard interface
- **Directive files** — methodology, teaching style, playbooks are just specs. They don't say "Claude should..." they say "the partner should..."
- **Profile system** — skills, history, identity are read/write state. Any model can consume and update them
- **Knowledge base** — reference material that's useful to humans and models equally

### Still Claude-Specific
- **CLAUDE.md** — the glue file that tells *this specific model* how to assemble everything. The orchestration logic lives in a prompt, not in code.
- **Tool invocation** — right now it's "Claude reads a playbook and decides to run nmap." The decision-making is in-context, not in-protocol.
- **Memory management** — when to update profile files, what to remember, how to calibrate. All vibes-based prompt engineering right now.

The gap between "works with Claude" and "works with anything" is smaller than it looks. It's mostly about moving orchestration from prompts into protocol.

## The Protocol

### Layer 1: Tools (gh0st-tools)

The bash/python toolkit. Already built. Already model-agnostic.

```
tools/
├── ghost-recon.sh          # Recon automation
├── ghost-listen.py         # Shell handler (daemon/client)
├── ghost-exploit.py        # Exploit framework
├── ghost-enum.py           # Post-exploitation enum
├── lib/                    # Shared library
├── exploits/               # Plugin exploit modules
└── enumscripts/            # Target-side scripts
```

**Key property**: Every tool is a CLI. Stdin/stdout. `[DATA]` lines for structured output. No model-specific assumptions. If you can run bash, you can use these.

### Layer 2: Knowledge (gh0st-k)

The reference library. Methodology, playbooks, privesc techniques, CVE database, payload catalogue.

```
directives/
├── cybersecurity-methodology.md    # The pentesting workflow
├── tool-playbooks.md               # How to use every tool
└── teaching-style.md               # Communication calibration spec
knowledge/
├── privesc-linux.md                # Privesc reference
├── payloads.md                     # Shell/payload catalogue
└── cve-database.md                 # Encountered CVEs
```

**Key property**: Pure reference material. A human can read these. A model can read these. They define *what to do* without assuming *who's doing it*.

### Layer 3: Memory (gh0st-mem)

Persistent state about the operator and the engagement history.

```
profile/
├── identity.md         # Who the operator is
├── skills.md           # What they know, what they're learning
└── history.md          # What we've done together
sessions/
└── YYYY-MM-DD-*.md     # Per-engagement logs
```

**Key property**: Read/write state with clear semantics. Any model that follows the update rules produces the same memory behavior. The operator's experience is continuous regardless of which model is driving.

### Layer 4: Protocol (gh0st-spec)

This is the missing piece. A specification that any model can follow to become a security partner. It defines:

1. **Engagement triggers** — "When given a target IP, do X. When asked a question, do Y."
2. **Tool orchestration** — "After recon, parse [DATA] lines for OPEN_PORTS. For each HTTP port, run gobuster."
3. **Memory protocol** — "Update skills.md after sessions. Update identity.md when operator shares personal info. Don't ask permission."
4. **Calibration** — "Read profile/skills.md. Adjust explanation depth. Don't over-explain tools marked 'comfortable'."
5. **Personality spec** — "Direct. Opinionated. Say 'that won't work because...' not 'you might consider...'"

Right now this lives in CLAUDE.md as a Claude-specific prompt. The protocol version would be a structured spec — something closer to an API contract than a system prompt.

## The MCP Shape

When this becomes an MCP server, the interface would look something like:

### Tools (things the model calls)
```
gh0st/recon          — Start recon on a target (wraps ghost-recon.sh)
gh0st/listen-start   — Start shell listener daemon
gh0st/listen-cmd     — Send command to caught shell
gh0st/listen-upload  — Upload file to target
gh0st/listen-download — Download file from target
gh0st/exploit-list   — List available exploit modules
gh0st/exploit-run    — Run an exploit module
gh0st/exploit-check  — Check if target is vulnerable
gh0st/enum           — Run post-exploitation enumeration
gh0st/enum-parse     — Parse enum output for privesc vectors
```

### Resources (things the model reads for context)
```
gh0st://methodology          — The pentesting workflow
gh0st://playbooks            — Tool usage patterns
gh0st://knowledge/privesc    — Privesc reference
gh0st://knowledge/payloads   — Payload catalogue
gh0st://knowledge/cves       — CVE database
gh0st://profile/skills       — Operator skill matrix
gh0st://profile/identity     — Operator profile
gh0st://session/current      — Active session state
```

### Prompts (things that shape the model's behavior)
```
gh0st://personality          — How to communicate
gh0st://calibration          — Read skills, adjust depth
gh0st://engagement-rules     — What to do in each context
```

Any MCP-compatible model connects, reads the resources, has the tools, follows the prompts — instant security partner. The operator's profile, history, and preferences carry over. No "getting to know you" phase. No context lost.

## Why This Matters

### The Immediate Win
We test with Ghost Girl on Claude. Everything we learn improves the tools, knowledge, and protocol. When we hit friction, we fix it. The protocol emerges from real engagements, not theoretical design.

### The Bigger Win
If the protocol works, anyone can:
- Fork the repo
- Point their model (Claude, GPT, Llama, whatever) at the MCP server
- Have a competent security partner immediately
- Their profile builds over time, making the partner better for *them*

### The Biggest Win
The protocol pattern isn't security-specific. The four layers — tools, knowledge, memory, spec — work for any domain where a human and AI collaborate persistently:
- Bug bounty hunting
- Red team operations
- Incident response
- Forensics
- Any technical discipline, really

gh0st-protocol is the security instantiation. The pattern is universal.

## What We're NOT Doing Yet

- Building the MCP server (premature — need more room-testing first)
- Supporting multiple models simultaneously (one partnership at a time)
- Building a web UI or SaaS product (this is a protocol, not a platform)
- Abstracting too early (the specifics of Ghost Girl inform the generality of the protocol)

## The Path

```
Phase 0 (DONE): Ghost Girl works with hardcoded Claude prompts
Phase 1 (NOW):  Ghost tools built, road-test through rooms, find friction
Phase 2 (NEXT): Extract protocol spec from what works
Phase 3:        Build MCP server wrapping the protocol
Phase 4:        Test with a second model to prove portability
Phase 5:        Open source the protocol. Let the community run with it.
```

We're in Phase 1. The right move is to go hack things, see what breaks, and let the protocol crystallize from practice. The vision is captured here so we don't lose the thread.

## Naming

Because we're us:

| Component | Name |
|-----------|------|
| The overall protocol | **gh0st-protocol** |
| The tool suite | **gh0st-tools** |
| The knowledge layer | **gh0st-k** |
| The memory system | **gh0st-mem** |
| The behavior spec | **gh0st-spec** |
| The MCP server (future) | **gh0st-mcp** |
| A running instance | **a gh0st** |
| The operator | **the summoner** |

> *"Every summoner gets the gh0st they deserve."*

---

*This document evolves. Updated as we learn from real engagements.*
