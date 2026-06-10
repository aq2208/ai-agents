# Simple Research Agent — Design Spec

**Date:** 2026-06-10
**Status:** Approved

## Overview

A research assistant AI agent built with Google Gemma 4, a `web_search` tool powered by Tavily, and a Gradio chat UI. The goal is to practice the full cycle: build → run locally → test in UI → deploy to AgentBase.

## File Structure

```
simple-agent/
├── agent.py                          # Agent loop: Gemma 4 + web_search tool
├── tools.py                          # web_search implementation via Tavily API
├── app.py                            # Gradio UI — wires chat input to agent
├── requirements.txt                  # gradio, google-generativeai, requests, python-dotenv
├── .env.example                      # GOOGLE_API_KEY, TAVILY_API_KEY
├── Dockerfile                        # Python 3.12 slim, runs app.py on 0.0.0.0:7860
└── greennode-agentbase-skills/       # Cloned from github.com/vngcloud/greennode-agentbase-skills
```

## Architecture

```
User (browser)
    ↓  types question
app.py  (Gradio ChatInterface)
    ↓  calls agent.run(question)
agent.py  (observe-think-act loop, max 10 iterations)
    ↓  sends message + tool definition to Gemma 4
google-generativeai SDK
    ↓  Gemma calls web_search(query)
tools.py  (Tavily API call)
    ↓  returns plain-text summary
agent.py  (appends result, loops back to Gemma)
    ↓  Gemma produces final answer
app.py  (streams answer into chat window)
```

## Components

### `agent.py`
- Stateless function `run(question: str) -> Generator[str, None, None]`
- Builds message history for the duration of one query
- Defines one tool: `web_search`
- Loops until `finish_reason == "stop"` or `max_iterations=10` reached
- Yields text chunks for streaming into the Gradio UI
- On max iterations: sends a final "give your best answer" prompt to Gemma

### `tools.py`
- Single function: `web_search(query: str) -> str`
- Calls the Tavily Search API (`POST https://api.tavily.com/search`)
- Returns a plain-text summary suitable for the agent to read
- On API failure: returns an error string (does not raise — agent handles gracefully)

### `app.py`
- `gr.ChatInterface` with a streaming response function
- Tool calls shown as intermediate chat messages before the final answer
- Run with: `python app.py` → available at `http://localhost:7860`

### `Dockerfile`
- Base: `python:3.12-slim`
- Copies source, installs `requirements.txt`
- Exposes port `7860`
- CMD: `python app.py`
- AgentBase deploy skill handles build + push

### `greennode-agentbase-skills/`
- Cloned from `https://github.com/vngcloud/greennode-agentbase-skills`
- Contains the `agentbase-deploy` skill used for deployment

## Error Handling

| Scenario | Behavior |
|---|---|
| `web_search` API failure | Tool returns error string; agent tells user gracefully |
| Gemma hits `max_iterations` | Agent asks Gemma for best answer with available context |
| Missing `.env` keys | `ValueError` raised at startup with a clear message |

## Local Development

```bash
cp .env.example .env      # fill in GOOGLE_API_KEY and TAVILY_API_KEY
pip install -r requirements.txt
python app.py             # opens at http://localhost:7860
```

## Testing

Manual testing via the Gradio UI:
1. Type a research question
2. Verify the agent calls `web_search` (visible as intermediate message)
3. Verify a coherent final answer is returned

## Deployment

Use the `agentbase-deploy` skill from `greennode-agentbase-skills/` after local testing passes.

## Dependencies

| Package | Purpose |
|---|---|
| `google-generativeai` | Gemma 4 API client |
| `gradio` | Chat UI |
| `requests` | Tavily API calls |
| `python-dotenv` | Load `.env` keys |
