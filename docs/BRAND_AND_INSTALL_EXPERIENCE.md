# Brand and install experience

AethOS first-impression standards: README, installer, terminal output, and terminology.

## Design tone

| Keyword | Meaning |
|---------|---------|
| Enterprise | Restrained, systems-grade, no hype |
| Operational | Lifecycle, evidence, audit — not chat novelty |
| Trustworthy | Preflight warnings, defaults safe, no hidden automation |
| Dark-native | Cyan governance · emerald runtime · slate enterprise |

**Avoid:** crypto aesthetics, emoji overload, hacker scripts, badge spam, duplicated labels.

## Badge system

### Primary row (identity)

- Governed Agentic OS — cyan (`#0891b2`)
- Operational Intelligence Platform — slate (`#334155`)
- Mission Control Runtime — emerald (`#047857`)

### Secondary row (specs)

- Apache 2.0 — cyan border
- Contributions Welcome — slate
- Python 3.11+ — emerald
- Mutation Governance — cyan
- Browser Evidence Engine — cyan deep

### Rules

- Unified height (`flat-square` on shields.io)
- Same label background (`#0f172a`)
- No duplicate “License” labels
- Max two rows above the fold

## Terminal brand constants

Python: `aethos_core/cli/brand.py`

| Constant | Use |
|----------|-----|
| `AETHOS_PRIMARY` | Identity, sections |
| `AETHOS_SUCCESS` | Completed steps |
| `AETHOS_WARNING` | Optional deps, ports in use |
| `AETHOS_MUTATION` | Mutation warnings |
| `AETHOS_EVIDENCE` | Browser / artifact logs |
| `AETHOS_SLATE` | Muted enterprise text |

Bash installer mirrors these ANSI values in `install.sh`.

## Install script UX

### Sections

1. Banner — product name + trust contract
2. Preflight — operating system, Git, Python, Node, disk, ports
3. Source — clone/update or use an existing tree without overwriting changes
4. Backend — venv, locked project metadata, `.env` preservation
5. Frontend — `npm ci`, `.env.local` preservation
6. Verification — API import, CLI, frontend type check
7. Success — URLs, doctor, status, help, recovery, and log path

### Required messages

- `[AethOS]` prefix on every line
- `Mutation execution disabled by default`
- Mission Control URLs on success
- Exact `--resume` / `-Resume` recovery command on failure
- Focused help and persistent progress for every stage

### Avoid

- Stack traces during normal install
- Emoji in installer output
- Verbose pip/npm unless `AETHOS_VERBOSE=1`

## Terminology discipline

| Prefer | Avoid |
|--------|-------|
| Governed execution preflight | Mutation execution mutation preflight |
| Mission Control | MC panel panel |
| Browser evidence | Browser browser capture |
| Engineering workspace | Local repo repo workspace |
| Provider runtime | Provider provider adapter |

## README structure (top fold)

1. Hero + badges
2. What / why / trust (3 sentences)
3. Install block + trust bullets
4. Architecture diagram
5. Capabilities table
6. Mission Control
7. Governance guarantees
8. Quick start + docs

## Screenshot standards

- Dark palette aligned with Mission Control (`#0f172a` base)
- Consistent crop width (1400px canvas)
- Subtle shadow, no heavy glow
- Emphasize orchestration + lifecycle, not chat bubbles

## Install philosophy

The install experience is the **first operational trust contract**:

- Defaults are safe (no mutations, no background automation)
- Output is concise and branded
- Next steps are operational (connect providers, register workspaces)
- Engineer understands *what*, *why different*, *why trustworthy* in under 60 seconds

## Files

| File | Role |
|------|------|
| `install.sh` | Remote + local installer |
| `install.ps1` | Native Windows remote + local installer |
| `run.sh` | Dev runtime launcher |
| `run.ps1` | Native Windows runtime launcher |
| `aethos_core/cli/brand.py` | Shared terminal identity |
| `README.md` | GitHub first impression |
