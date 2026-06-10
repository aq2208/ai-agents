# Design Spec — AgentBase Sample Agent (Platform Onboarding)

#spec #agentbase #vng-hackathon

**Date:** 2026-06-10  
**Project dir:** `ai-agents/simple-agent/`  
**Related:** [[Projects/Hackathon]]

---

## Goal

Build and deploy a minimal Q&A bot on VNG's AgentBase platform. The purpose is **platform onboarding** — not building a production agent. By the end, we should understand:

- How to install and use the AgentBase Claude Code skills
- How to configure a platform-provided LLM
- The full scaffold → configure → deploy → verify lifecycle
- How to monitor a running agent

This sample is the foundation for the real hackathon agent ([[Projects/Hackathon]]).

---

## Architecture

```
User message
    ↓
AgentBase Runtime (managed)
    ↓
Platform LLM (no external API key required)
    ↓
Response
```

No tools, no memory, no RAG. Pure request → LLM → response. The platform handles all orchestration; we only configure and deploy.

---

## Approach: Platform-Native Wizard

Use the AgentBase Claude Code skills (`/agentbase-wizard` and friends) to scaffold, configure, and deploy the agent. Minimal custom code — the wizard generates the project structure and the platform manages the runtime.

**Why this approach:** The goal is to learn the platform, not write infrastructure. The wizard covers the full lifecycle and forces us to touch every major platform concept (LLM config, identity, runtime, monitoring).

---

## Components & Deliverables

### 1. Deployed Agent (`simple-agent/`)
- Scaffolded via `/agentbase-wizard`
- Platform LLM configured via `/agentbase-llm`
- Identity registered via `/agentbase-identity`
- Runtime deployed via `/agentbase-deploy`
- Live and verified on the AI Portal

### 2. Guideline Document (`vault/Tools/AgentBase Platform Guide.md`)
- Step-by-step walkthrough: install → configure → plan → develop → deploy → monitor
- Analysis of each AgentBase skill: purpose, key commands, when to use
- Real commands and outputs from this session
- Gotchas and non-obvious decisions

---

## Setup & Deployment Flow

| Step | Command / Action | What it does |
|------|-----------------|--------------|
| 1 | Clone `greennode-agentbase-skills` | Get the skill files |
| 2 | Copy skills to `~/.claude/skills/` | Install into Claude Code |
| 3 | Export `GREENNODE_CLIENT_ID` + `GREENNODE_CLIENT_SECRET` | Authenticate to platform |
| 4 | Run `/agentbase-wizard` in `simple-agent/` | 9-step guided scaffold + deploy |
| 5 | `/agentbase-llm api-keys create` | Connect to a platform model |
| 6 | `/agentbase-identity` | Register agent identity |
| 7 | `/agentbase-deploy deploy` | Build, push, deploy runtime |
| 8 | Verify on AI Portal | Send a test Q&A message |
| 9 | `/agentbase-monitor runtime-logs` | Confirm logs are flowing |
| 10 | Write `vault/Tools/AgentBase Platform Guide.md` | Document what we learned |

---

## Mode: Guided Learning

The user executes every command themselves. Claude explains:
- What each step does and why it exists
- What the platform is doing behind the scenes
- What to watch for in the output
- How each skill connects to the broader platform architecture

---

## Prerequisites

- [ ] `GREENNODE_CLIENT_ID` and `GREENNODE_CLIENT_SECRET` available
- [ ] Docker installed and running (needed for `/agentbase-deploy`)
- [ ] Claude Code with internet access (to clone the skills repo)
- [ ] Access to `aiplatform.console.vngcloud.vn`

---

## Out of Scope

- Custom agent logic / Python code
- Tools, memory, RAG — all deferred to the real hackathon agent
- CI/CD pipeline
- Multi-turn conversation state

---

## Related Notes

- [[Tools/AgentBase Platform Guide]] — written after the session
- [[Projects/Hackathon]] — the real agent this onboarding feeds into
