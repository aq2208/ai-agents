# Simple Research Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a research assistant agent using Gemma 4 + Tavily web search, with a Gradio chat UI, testable locally and deployable to AgentBase.

**Architecture:** `agent.py` runs an observe-think-act loop calling Gemma 4 via `google-generativeai`; when Gemma requests a tool call, `tools.py` hits the Tavily API; `app.py` wraps the generator in a Gradio `ChatInterface` for browser-based testing.

**Tech Stack:** Python 3.12, `google-generativeai`, `gradio`, `requests`, `python-dotenv`, `pytest`

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `requirements.txt` | Create | All Python dependencies |
| `.env.example` | Create | Required environment variable keys |
| `tests/__init__.py` | Create | Makes tests/ a package |
| `tests/conftest.py` | Create | sys.path setup for imports |
| `tools.py` | Create | `web_search(query) -> str` via Tavily API |
| `tests/test_tools.py` | Create | Unit tests for tools.py |
| `agent.py` | Create | `run(question) -> Generator` — Gemma 4 agent loop |
| `tests/test_agent.py` | Create | Unit tests for agent.py |
| `app.py` | Create | Gradio ChatInterface wired to agent.run() |
| `Dockerfile` | Create | Container for AgentBase deployment |
| `greennode-agentbase-skills/` | Clone | AgentBase deploy skill |

---

## Task 1: Project Bootstrap

**Files:**
- Create: `simple-agent/requirements.txt`
- Create: `simple-agent/.env.example`
- Create: `simple-agent/tests/__init__.py`
- Create: `simple-agent/tests/conftest.py`

- [ ] **Step 1: Create requirements.txt**

```
google-generativeai>=0.8.0
gradio>=4.44.0
requests>=2.31.0
python-dotenv>=1.0.0
pytest>=8.0.0
```

Save to `simple-agent/requirements.txt`.

- [ ] **Step 2: Create .env.example**

```
GOOGLE_API_KEY=your-google-ai-studio-api-key-here
TAVILY_API_KEY=your-tavily-api-key-here
```

Save to `simple-agent/.env.example`.

Get a free Tavily key at https://tavily.com — free tier covers 1000 searches/month.
Get a Google AI Studio key at https://aistudio.google.com/apikey.

- [ ] **Step 3: Create tests/__init__.py**

Create `simple-agent/tests/__init__.py` as an empty file.

- [ ] **Step 4: Create tests/conftest.py**

```python
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
```

Save to `simple-agent/tests/conftest.py`.

- [ ] **Step 5: Install dependencies and verify**

```bash
cd simple-agent
pip install -r requirements.txt
python -c "import google.generativeai, gradio, requests, dotenv; print('OK')"
```

Expected output: `OK`

- [ ] **Step 6: Commit**

```bash
git add simple-agent/requirements.txt simple-agent/.env.example simple-agent/tests/__init__.py simple-agent/tests/conftest.py
git commit -m "feat: bootstrap simple-agent project structure"
```

---

## Task 2: Implement web_search Tool (TDD)

**Files:**
- Create: `simple-agent/tests/test_tools.py`
- Create: `simple-agent/tools.py`

- [ ] **Step 1: Write the failing tests**

```python
# simple-agent/tests/test_tools.py
from unittest.mock import patch, Mock
import pytest
from tools import web_search


def test_web_search_returns_answer_field_when_present():
    mock_resp = Mock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = {
        "answer": "Python is a high-level programming language.",
        "results": [],
    }
    with patch("tools.requests.post", return_value=mock_resp):
        result = web_search("what is python")
    assert result == "Python is a high-level programming language."


def test_web_search_falls_back_to_results_when_no_answer():
    mock_resp = Mock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = {
        "answer": "",
        "results": [
            {"title": "Python Docs", "content": "Python is a programming language."}
        ],
    }
    with patch("tools.requests.post", return_value=mock_resp):
        result = web_search("python")
    assert "Python Docs" in result
    assert "programming language" in result


def test_web_search_returns_error_string_on_exception():
    with patch("tools.requests.post", side_effect=Exception("network timeout")):
        result = web_search("query")
    assert "error" in result.lower()
    assert "network timeout" in result
```

Save to `simple-agent/tests/test_tools.py`.

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd simple-agent
pytest tests/test_tools.py -v
```

Expected: 3 FAILED with `ModuleNotFoundError: No module named 'tools'`

- [ ] **Step 3: Implement tools.py**

```python
# simple-agent/tools.py
import os
import requests

_TAVILY_URL = "https://api.tavily.com/search"


def web_search(query: str) -> str:
    try:
        resp = requests.post(
            _TAVILY_URL,
            json={
                "api_key": os.environ["TAVILY_API_KEY"],
                "query": query,
                "search_depth": "basic",
                "max_results": 3,
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("answer"):
            return data["answer"]
        return "\n\n".join(
            f"{r['title']}: {r['content']}" for r in data.get("results", [])[:3]
        )
    except Exception as e:
        return f"Search error: {e}"
```

Save to `simple-agent/tools.py`.

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd simple-agent
pytest tests/test_tools.py -v
```

Expected: 3 PASSED

- [ ] **Step 5: Commit**

```bash
git add simple-agent/tools.py simple-agent/tests/test_tools.py
git commit -m "feat: implement web_search tool with Tavily API"
```

---

## Task 3: Implement Agent Loop (TDD)

**Files:**
- Create: `simple-agent/tests/test_agent.py`
- Create: `simple-agent/agent.py`

- [ ] **Step 1: Write the failing tests**

```python
# simple-agent/tests/test_agent.py
from unittest.mock import patch, MagicMock
import agent


def _text_response(text: str):
    """Builds a mock Gemma response with no function call."""
    part = MagicMock()
    part.function_call = None
    part.text = text
    resp = MagicMock()
    resp.parts = [part]
    resp.text = text
    return resp


def _tool_call_response(fn_name: str, fn_args: dict):
    """Builds a mock Gemma response requesting a tool call."""
    fn_call = MagicMock()
    fn_call.name = fn_name
    fn_call.args = fn_args
    part = MagicMock()
    part.function_call = fn_call
    resp = MagicMock()
    resp.parts = [part]
    resp.text = ""
    return resp


def test_run_yields_final_answer_when_no_tool_call():
    final = _text_response("Paris is the capital of France.")
    with patch("agent.genai.configure"), \
         patch("agent.genai.GenerativeModel") as mock_cls:
        mock_model = MagicMock()
        mock_cls.return_value = mock_model
        mock_chat = MagicMock()
        mock_model.start_chat.return_value = mock_chat
        mock_chat.send_message.return_value = final

        results = list(agent.run("What is the capital of France?"))

    assert results == ["Paris is the capital of France."]


def test_run_calls_tool_then_yields_final_answer():
    tool_resp = _tool_call_response("web_search", {"query": "capital of France"})
    final = _text_response("Paris.")
    mock_search = MagicMock(return_value="Paris is the capital of France.")

    with patch("agent.genai.configure"), \
         patch("agent.genai.GenerativeModel") as mock_cls, \
         patch.dict("agent.AVAILABLE_TOOLS", {"web_search": mock_search}):
        mock_model = MagicMock()
        mock_cls.return_value = mock_model
        mock_chat = MagicMock()
        mock_model.start_chat.return_value = mock_chat
        mock_chat.send_message.side_effect = [tool_resp, final]

        results = list(agent.run("What is the capital of France?"))

    mock_search.assert_called_once_with(query="capital of France")
    assert any("Searching" in r for r in results)
    assert results[-1] == "Paris."
```

Save to `simple-agent/tests/test_agent.py`.

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd simple-agent
pytest tests/test_agent.py -v
```

Expected: 2 FAILED with `ModuleNotFoundError: No module named 'agent'`

- [ ] **Step 3: Implement agent.py**

```python
# simple-agent/agent.py
import os
import google.generativeai as genai
from google.generativeai.types import FunctionDeclaration, Tool
from tools import web_search

_SYSTEM_PROMPT = (
    "You are a helpful research assistant. Use the web_search tool to find "
    "current information when needed. When you have enough to answer the user's "
    "question fully, respond directly without calling more tools."
)

_WEB_SEARCH_TOOL = Tool(function_declarations=[
    FunctionDeclaration(
        name="web_search",
        description="Search the web for current information on a topic.",
        parameters={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query to look up",
                }
            },
            "required": ["query"],
        },
    )
])

AVAILABLE_TOOLS = {"web_search": web_search}
MAX_ITERATIONS = 10


def run(question: str):
    """Run the research agent. Yields status updates then the final answer."""
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
    model = genai.GenerativeModel(
        model_name="gemma-4-12b-it",
        tools=[_WEB_SEARCH_TOOL],
        system_instruction=_SYSTEM_PROMPT,
    )
    chat = model.start_chat()
    response = chat.send_message(question)

    for _ in range(MAX_ITERATIONS):
        fn_calls = [
            p for p in response.parts
            if p.function_call and p.function_call.name
        ]
        if not fn_calls:
            yield response.text
            return

        for part in fn_calls:
            fn = part.function_call
            yield f"🔍 Searching: **{fn.args['query']}**\n\n"
            result = AVAILABLE_TOOLS[fn.name](**dict(fn.args))
            response = chat.send_message(
                genai.protos.Part(
                    function_response=genai.protos.FunctionResponse(
                        name=fn.name,
                        response={"result": result},
                    )
                )
            )

    yield f"*(reached max {MAX_ITERATIONS} iterations)*\n\n{response.text}"
```

Save to `simple-agent/agent.py`.

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd simple-agent
pytest tests/test_agent.py -v
```

Expected: 2 PASSED

- [ ] **Step 5: Run all tests**

```bash
cd simple-agent
pytest tests/ -v
```

Expected: 5 PASSED

- [ ] **Step 6: Commit**

```bash
git add simple-agent/agent.py simple-agent/tests/test_agent.py
git commit -m "feat: implement Gemma 4 agent loop with web_search tool"
```

---

## Task 4: Build Gradio UI

**Files:**
- Create: `simple-agent/app.py`

- [ ] **Step 1: Implement app.py**

```python
# simple-agent/app.py
import os
from dotenv import load_dotenv
import gradio as gr
import agent

load_dotenv()


def _validate_env() -> None:
    missing = [k for k in ("GOOGLE_API_KEY", "TAVILY_API_KEY") if not os.getenv(k)]
    if missing:
        raise ValueError(f"Missing environment variables: {', '.join(missing)}")


def respond(message: str, history: list):
    """Gradio streaming response — each yield is the full accumulated text so far."""
    accumulated = ""
    for chunk in agent.run(message):
        accumulated += chunk
        yield accumulated


demo = gr.ChatInterface(
    fn=respond,
    title="Research Assistant",
    description="Ask me anything — I'll search the web to find the answer.",
)

if __name__ == "__main__":
    _validate_env()
    demo.launch(server_name="0.0.0.0", server_port=7860)
```

Save to `simple-agent/app.py`.

- [ ] **Step 2: Copy .env.example and fill in keys**

```bash
cd simple-agent
cp .env.example .env
# Edit .env and add your real GOOGLE_API_KEY and TAVILY_API_KEY
```

- [ ] **Step 3: Run the app and test manually**

```bash
cd simple-agent
python app.py
```

Expected output:
```
Running on local URL:  http://0.0.0.0:7860
```

Open `http://localhost:7860` in your browser. Type: `What is the latest news about AI?`

Verify:
1. A `🔍 Searching: **...**` line appears first
2. A coherent final answer appears after

- [ ] **Step 4: Commit**

```bash
git add simple-agent/app.py
git commit -m "feat: add Gradio chat UI for research agent"
```

---

## Task 5: Dockerfile

**Files:**
- Create: `simple-agent/Dockerfile`

- [ ] **Step 1: Create Dockerfile**

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 7860

CMD ["python", "app.py"]
```

Save to `simple-agent/Dockerfile`.

- [ ] **Step 2: Build the image**

```bash
cd simple-agent
docker build -t simple-agent:local .
```

Expected: `Successfully built ...` (or `Successfully tagged simple-agent:local`)

- [ ] **Step 3: Run the container locally to verify**

```bash
docker run --rm \
  -e GOOGLE_API_KEY="$(grep GOOGLE_API_KEY .env | cut -d= -f2)" \
  -e TAVILY_API_KEY="$(grep TAVILY_API_KEY .env | cut -d= -f2)" \
  -p 7860:7860 \
  simple-agent:local
```

Open `http://localhost:7860` and send a test message. Verify it works identically to running `python app.py` directly.

- [ ] **Step 4: Commit**

```bash
git add simple-agent/Dockerfile
git commit -m "feat: add Dockerfile for AgentBase deployment"
```

---

## Task 6: Clone AgentBase Skills and Deploy

**Files:**
- Clone into: `simple-agent/greennode-agentbase-skills/`

- [ ] **Step 1: Clone the AgentBase skills repo**

```bash
cd simple-agent
git clone https://github.com/vngcloud/greennode-agentbase-skills greennode-agentbase-skills
```

Expected: A `greennode-agentbase-skills/` directory appears inside `simple-agent/`.

- [ ] **Step 2: Add greennode-agentbase-skills to .gitignore (optional)**

If you don't want to commit the cloned skills as part of this repo, add it to `.gitignore`:

```
greennode-agentbase-skills/
.env
```

Save to `simple-agent/.gitignore`.

- [ ] **Step 3: Follow the agentbase-deploy skill**

Open the `agentbase-deploy` skill from the cloned directory and follow its instructions to deploy.

The skill is at: `simple-agent/greennode-agentbase-skills/` — check for a `agentbase-deploy` skill file or README.

- [ ] **Step 4: Commit .gitignore**

```bash
git add simple-agent/.gitignore
git commit -m "chore: add .gitignore for simple-agent"
```
