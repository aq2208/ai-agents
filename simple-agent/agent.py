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
    genai.configure(api_key=os.environ.get("GOOGLE_API_KEY", ""))
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
