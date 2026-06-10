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
        with patch.dict("os.environ", {"TAVILY_API_KEY": "test_key"}):
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
        with patch.dict("os.environ", {"TAVILY_API_KEY": "test_key"}):
            result = web_search("python")
    assert "Python Docs" in result
    assert "programming language" in result


def test_web_search_returns_error_string_on_exception():
    with patch("tools.requests.post", side_effect=Exception("network timeout")):
        with patch.dict("os.environ", {"TAVILY_API_KEY": "test_key"}):
            result = web_search("query")
    assert "error" in result.lower()
    assert "network timeout" in result
