# AgentBase Sample Agent — Implementation Plan

> **Mode:** Guided learning. You execute every command. Claude explains what each step does and why.

**Goal:** Deploy a minimal Q&A bot on VNG's AgentBase platform to learn the full agent lifecycle.

**Architecture:** Platform-native wizard approach — the AgentBase Claude Code skills scaffold the project, configure a platform-provided LLM, and deploy a managed runtime. Zero custom code.

**Tech Stack:** VNG AgentBase platform, `greennode-agentbase-skills` Claude Code skills, Docker (for image build/push), AI Portal (`aiplatform.console.vngcloud.vn`)

---

## Task 1: Install AgentBase Skills

**Files:**
- Create: `~/.claude/skills/` (populated from cloned repo)

- [ ] **Step 1: Clone the skills repo**

```bash
cd ~
git clone https://github.com/vngcloud/greennode-agentbase-skills.git
```

Expected: repo cloned to `~/greennode-agentbase-skills/`

- [ ] **Step 2: Copy skills into Claude Code**

```bash
mkdir -p ~/.claude/skills
cp -r ~/greennode-agentbase-skills/.claude/skills/* ~/.claude/skills/
```

- [ ] **Step 3: Verify skills are installed**

```bash
ls ~/.claude/skills/
```

Expected: you should see skill files like `agentbase-wizard.md`, `agentbase-deploy.md`, `agentbase-llm.md`, etc.

- [ ] **Step 4: Restart Claude Code**

Close and reopen Claude Code so it picks up the new skills. After restart, skills like `/agentbase-wizard` and `/agentbase-deploy` will be available as slash commands.

- [ ] **Step 5: Commit baseline**

```bash
cd ~/Documents/Repositories/ai-agents/simple-agent
git add .
git commit -m "chore: start agentbase sample agent onboarding"
```

---

## Task 2: Set Up Credentials

- [ ] **Step 1: Export your GreenNode service account credentials**

```bash
export GREENNODE_CLIENT_ID="<your-service-account-id>"
export GREENNODE_CLIENT_SECRET="<your-service-account-secret>"
```

Replace with your actual values. These are the credentials for the VNG AI Portal service account.

- [ ] **Step 2: Verify they are set**

```bash
echo "CLIENT_ID: $GREENNODE_CLIENT_ID"
echo "SECRET set: $([ -n "$GREENNODE_CLIENT_SECRET" ] && echo yes || echo NO)"
```

Expected:
```
CLIENT_ID: <your-id>
SECRET set: yes
```

> **Note:** These are shell session variables. If you open a new terminal, you'll need to export them again. Consider adding them to your `~/.zshrc` or a `.env` file (never commit secrets).

---

## Task 3: Scaffold the Agent with the Wizard

- [ ] **Step 1: Navigate to the project directory**

```bash
cd ~/Documents/Repositories/ai-agents/simple-agent
```

- [ ] **Step 2: Invoke the AgentBase wizard**

In Claude Code, type:
```
/agentbase-wizard
```

The wizard will guide you through a 9-step lifecycle: scaffold → configure → code → test → deploy → verify.

- [ ] **Step 3: Follow the wizard — Project Initialization**

When prompted for a project name, use: `simple-qa-agent`

When asked for a description, use something like:
```
A minimal Q&A bot for learning the AgentBase platform.
```

- [ ] **Step 4: Follow the wizard — Agent Type**

Select the simplest agent type available (conversational / Q&A / no tools). The wizard may call this a "basic agent" or "conversational agent".

- [ ] **Step 5: Observe the scaffolded files**

```bash
ls ~/Documents/Repositories/ai-agents/simple-agent/
```

The wizard will have created files like:
- `agent.yaml` or `agentbase.yaml` — agent configuration
- `Dockerfile` — for building the runtime image
- `main.py` or `app.py` — minimal agent entrypoint
- `requirements.txt` — Python dependencies

- [ ] **Step 6: Commit the scaffold**

```bash
git add .
git commit -m "feat: scaffold simple-qa-agent via agentbase-wizard"
```

---

## Task 4: Configure LLM Access

- [ ] **Step 1: Invoke the LLM skill**

In Claude Code:
```
/agentbase-llm
```

- [ ] **Step 2: List available platform models**

Follow the skill prompts to list models available on the platform. Note the model IDs shown — these are VNG-hosted models you can use without an external API key.

- [ ] **Step 3: Configure the agent to use a platform model**

When prompted, select a model (preferably the default or recommended one). The skill will update your `agent.yaml` / config with the model reference.

- [ ] **Step 4: Verify the config was updated**

Open `agent.yaml` (or whichever config file was generated) and confirm it now references the selected model.

- [ ] **Step 5: Commit**

```bash
git add .
git commit -m "feat: configure platform LLM for simple-qa-agent"
```

---

## Task 5: Register Agent Identity

- [ ] **Step 1: Invoke the identity skill**

In Claude Code:
```
/agentbase-identity
```

- [ ] **Step 2: Register the agent**

Follow the prompts to register `simple-qa-agent` as an identity on the platform. This creates a unique agent ID on the portal that links deployments, logs, and credentials together.

- [ ] **Step 3: Note the agent ID**

The skill will output an agent ID or resource name. Copy it — you'll use it to find your agent on the portal.

- [ ] **Step 4: Commit any config changes**

```bash
git add .
git commit -m "feat: register simple-qa-agent identity on AgentBase"
```

---

## Task 6: Deploy the Agent

- [ ] **Step 1: Make sure Docker is running**

```bash
docker info | head -5
```

Expected: Docker version info. If you see "Cannot connect to the Docker daemon", start Docker Desktop first.

- [ ] **Step 2: Invoke the deploy skill**

In Claude Code:
```
/agentbase-deploy deploy
```

- [ ] **Step 3: Watch the build output**

The skill will:
1. Build a Docker image from the `Dockerfile`
2. Push it to VNG's container registry
3. Create or update the Custom Agent runtime on the platform

This takes 2–5 minutes. Watch for any errors during the image build or push.

- [ ] **Step 4: Confirm deployment success**

The skill should output a deployment status and a URL or agent endpoint. Note the endpoint URL.

- [ ] **Step 5: Commit**

```bash
git add .
git commit -m "feat: deploy simple-qa-agent to AgentBase platform"
```

---

## Task 7: Verify on the AI Portal

- [ ] **Step 1: Open the portal**

Navigate to `https://aiplatform.console.vngcloud.vn/overview` in your browser.

- [ ] **Step 2: Locate your agent**

Find the Agent section (likely under "Agents" or "Custom Agents"). Look for `simple-qa-agent` or the agent ID from Task 5.

- [ ] **Step 3: Send a test message**

Use the portal's built-in chat interface (if available) to send a test question, for example:
```
What is the capital of France?
```

Expected: the agent responds with "Paris" or similar. This confirms the full path (portal → runtime → LLM → response) is working.

- [ ] **Step 4: Try a second message**

```
Explain what an AI agent is in one sentence.
```

Expected: a coherent one-sentence answer. This confirms the LLM is properly connected.

---

## Task 8: Monitor Runtime Logs

- [ ] **Step 1: Invoke the monitor skill**

In Claude Code:
```
/agentbase-monitor runtime-logs
```

- [ ] **Step 2: Observe the log output**

You should see log entries for the two test messages you sent in Task 7 — request received, LLM call made, response returned.

- [ ] **Step 3: Check for errors**

Scan for any `ERROR` or `WARN` lines. For a simple Q&A bot with no tools, there should be none.

---

## Task 9: Write the AgentBase Platform Guide

- [ ] **Step 1: Create the guide file**

Create `vault/Tools/AgentBase Platform Guide.md` with the following structure (fill in from what you observed during Tasks 1–8):

```markdown
# AgentBase Platform Guide

## What is AgentBase?
[Brief description of the platform — Models, Runtime, Memory, RAG, Guardrails, etc.]

## Prerequisites
- GreenNode credentials (GREENNODE_CLIENT_ID, GREENNODE_CLIENT_SECRET)
- Docker
- Claude Code with agentbase skills installed

## Installing the Skills
[Commands from Task 1]

## The Development Lifecycle
[Step-by-step from Tasks 2–8, with real commands and outputs you observed]

## AgentBase Skills Reference

### /agentbase-wizard
[What it does, when to use it, key steps it covers]

### /agentbase-llm
[What it does, how to list and select models]

### /agentbase-identity
[What it does, what an "agent identity" is on the platform]

### /agentbase-deploy
[What it does, what it builds, how to push]

### /agentbase-monitor
[What it does, how to read logs]

### /agentbase-memory
[What it does — even if unused in this sample]

### /agentbase-gateway
[What it does — resource/MCP gateway]

### /agentbase-policy
[What it does — authorization/access control]

### /agentbase-teardown
[What it does — cleanup/delete all resources]

## Gotchas & Non-Obvious Things
[Things you ran into or found surprising during this session]

## Next Steps — Real Hackathon Agent
[Link to [[Projects/Hackathon]] and what you'll build next]
```

- [ ] **Step 2: Commit the guide**

```bash
cd ~/Documents/Repositories/ai-agents
git add vault/Tools/AgentBase\ Platform\ Guide.md
git commit -m "docs: add AgentBase platform guide from onboarding session"
```

---

## Completion Checklist

- [ ] AgentBase skills installed and visible in Claude Code
- [ ] Credentials configured
- [ ] Agent scaffolded in `simple-agent/`
- [ ] Platform LLM connected
- [ ] Agent identity registered on portal
- [ ] Agent deployed and live
- [ ] Test Q&A messages verified on portal
- [ ] Runtime logs confirmed
- [ ] `vault/Tools/AgentBase Platform Guide.md` written and committed

---

## Related

- [[Projects/2026-06-10-agentbase-sample-agent-design]] — the design spec
- [[Projects/Hackathon]] — the real agent to build next
- [[Tools/AgentBase Platform Guide]] — written at the end of this plan
