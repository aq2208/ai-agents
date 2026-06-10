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
