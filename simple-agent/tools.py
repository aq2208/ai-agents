import os
import requests

_TAVILY_URL = "https://api.tavily.com/search"


def web_search(query: str) -> str:
    try:
        resp = requests.post(
            _TAVILY_URL,
            json={
                "api_key": os.environ.get("TAVILY_API_KEY", ""),
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
