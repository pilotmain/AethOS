# AethOS launch & discoverability kit

Ready-to-paste copy for getting AethOS in front of people. Discoverability is two games:
**(A) on-GitHub** (topics, homepage, social image, stars) and **(B) off-GitHub outreach**
(the channels below are where real traffic actually comes from). Post as a genuine
maintainer sharing a project — not as an ad. Never spam; one post per community, engage
in the comments.

Repo: https://github.com/pilotmain/AethOS · Site: https://pilotmain.com

---

## 0. Pre-launch checklist (do these first)

- [x] Add GitHub topics (agentic-ai, ai-agents, llmops, self-hosted, devops, …)
- [x] Set repo homepage → https://pilotmain.com
- [x] Enable GitHub Discussions
- [x] Plain-language, keyword-rich intro line in README
- [ ] Upload custom **social preview image** (Settings → General → Social preview). Use `docs/marketing/social-preview.png` once generated. *(GitHub has no API for this — must be done in the web UI.)*
- [ ] Record a 30–60s screen capture of Mission Control approving a mutation → convert to GIF for README + posts
- [ ] Make sure `main` CI is green (the "Python tests + lint" job currently fails/times out — fix before launch so the repo doesn't look broken)
- [ ] Pin a "Roadmap" or "Introduce yourself" Discussion

---

## 1. Hacker News — "Show HN"

**Title** (keep it plain; HN hates hype):
```
Show HN: AethOS – a self-hosted AI agent for cloud ops with human approval
```

**URL:** https://github.com/pilotmain/AethOS

**First comment** (post immediately after submitting — this is where HN reads context):
```
I built AethOS because I wanted an AI agent that could actually operate my
infrastructure (Railway, Vercel, GitHub) without the "unrestricted shell that
YOLOs your prod" problem.

Every action runs through a governed lifecycle: the agent does read-only analysis
first, then any mutation (restart, redeploy, stop, env var change) becomes a
*preflight* job that does nothing until I approve it in a Mission Control UI.
Nothing touches your providers unless execution flags are on AND you approve.
No auto-merge, no silent background coding, evidence + audit trail on everything.

It's Apache-2.0, self-hosted, and runs local-first. You bring your own LLM key
(Claude/OpenAI/OpenRouter) or a local model. Default config is deliberately
"off" for anything that mutates or touches the network.

Honest status: the governed cloud-ops core works when configured; the wider
workspace/voice/multi-channel surfaces are partially wired and flag-gated. Docs
are candid about what's proven vs. in-progress.

Would love feedback on the governance model — especially from people who've been
burned by an agent doing something destructive.
```

Tips: submit Tue–Thu ~8–10am ET. Don't ask for upvotes (bannable). Reply to every comment.

---

## 2. Reddit

Each subreddit wants a slightly different angle. Read each sub's self-promo rules first.

### r/selfhosted
**Title:** `AethOS – self-hosted, open-source AI agent for cloud ops (Railway/Vercel/GitHub) with human-in-the-loop approval`
**Body:**
```
Sharing a project I've been building: AethOS, an Apache-2.0 self-hosted agent that
runs infra tasks through your own LLM key, but gates every mutation behind an
approval step in a local Mission Control UI. Read-only by default; nothing deploys
or stops without you clicking approve.

Runs local-first (Docker or bare Python), bring your own Claude/OpenAI/OpenRouter
or local model. No telemetry by default.

Repo: https://github.com/pilotmain/AethOS
Happy to answer setup questions.
```

### r/LocalLLaMA
**Angle:** local-model support + agent governance.
**Title:** `Governed agentic ops runtime that works with local models — approval-gated mutations, no unrestricted shell`
**Body:** emphasize model-agnostic provider (OpenRouter/local), the deterministic router vs. tool-loop, and that it won't run destructive actions autonomously.

### r/devops
**Angle:** the "AI won't wreck prod" governance story. Show the preflight → approve → execute → verify flow. Lead with a screenshot/GIF.

### r/opensource
**Angle:** Apache-2.0, contribution-friendly, CONTRIBUTING/GOVERNANCE present, looking for early contributors.

---

## 3. X / Twitter thread

```
1/ I open-sourced AethOS: a self-hosted AI agent that can operate your cloud infra
(Railway, Vercel, GitHub) — but can't touch prod without your approval.

Apache-2.0. Bring your own LLM key. 🧵

2/ The problem with "AI + shell access" is obvious: one bad tool call and your
production is gone. AethOS fixes this with a governed lifecycle:

read-only analysis → preflight job → you approve in Mission Control → execute → verify → audit

3/ Default config is OFF for anything mutating or network-facing. The agent
proposes; you dispose. No auto-merge, no silent background coding, evidence on
every action.

4/ Works with Claude / OpenAI / OpenRouter / local models. Local-first, no
telemetry by default. One-line install for macOS/Linux/Windows.

5/ It's early and I'm honest about what's proven vs in-progress. If you've ever been
nervous handing an agent real credentials, I'd love your feedback.

⭐ https://github.com/pilotmain/AethOS
```

Attach the Mission Control GIF to tweet 1. Cross-post to LinkedIn as a single paragraph + link.

---

## 4. dev.to / Hashnode article (outline)

Title: **"Giving an AI agent access to my production infra — safely"**
- The fear: agents + credentials + prod
- The governance model (preflight → approve → execute → verify), with the ASCII diagram
- Walkthrough: register a target, ask "stop killit", approve in Mission Control
- What's flag-gated and why default-off matters
- Roadmap + call for contributors
- Canonical link back to the repo (helps SEO)

---

## 5. "Awesome" list PRs (steady long-tail discovery)

Being listed in these drives ongoing traffic. Fork, add one line in the right
category, open a PR that follows each list's exact format.

**awesome-ai-agents / awesome-autonomous-agents:**
```
- [AethOS](https://github.com/pilotmain/AethOS) - Self-hosted, governed agentic OS for cloud operations; every mutation is approval-gated with full evidence and audit. Apache-2.0.
```

**awesome-selfhosted** (their format: `- [Name](url) - Description. ([Demo](...)) ([Source Code](...)) \`License\` \`Language\``):
```
- [AethOS](https://github.com/pilotmain/AethOS) - Governed AI agent for self-hosted cloud/DevOps operations with human-in-the-loop approval. `Apache-2.0` `Python`
```
(Note: awesome-selfhosted requires the project be self-hostable and typically 6+ months old / non-trivial — check current CONTRIBUTING before submitting.)

**awesome-llmops / awesome-mcp-servers (if MCP support qualifies):**
```
- [AethOS](https://github.com/pilotmain/AethOS) - Agentic operations runtime with governed mutations across Railway/Vercel/GitHub. Apache-2.0.
```

---

## 6. Other channels

- **Product Hunt** — launch once the UI polish (single-shell + theming) lands; needs the GIF + gallery images.
- **Lobsters** (if you have an invite) — same as Show HN, tag `ai`, `devops`.
- **r/artificial, r/MachineLearning (Sat "What are you working on")**, **Ycombinator/Startup School** communities.
- **Comparison SEO**: a short docs page "AethOS vs. running an agent with raw shell access" captures people searching for safe agent alternatives.

---

## 7. Cadence

- Week 1: Show HN (once) + r/selfhosted + X thread. Respond to everything.
- Week 2: r/LocalLLaMA + r/devops + dev.to article.
- Week 3: awesome-list PRs + LinkedIn + comparison docs page.
- Ongoing: ship visible releases (tag them), post short changelogs, keep CI green.

Stars compound: GitHub search and most "awesome" aggregators rank by stars, so the
first 50–100 genuine stars from these posts materially change how findable the repo is.
