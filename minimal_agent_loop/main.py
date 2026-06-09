import json
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI()

# --- Tool definitions ---
tools = [
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Search the web for current information on a topic. "
                           "Use this when you need up-to-date facts or news.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to look up"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Evaluate a mathematical expression and return the result. "
                           "Use this for any arithmetic, unit conversions, or numerical reasoning.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "A valid Python math expression, e.g. '22 * 9/5 + 32'"
                    }
                },
                "required": ["expression"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a local text file by path.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The file path to read, e.g. './notes.txt'"
                    }
                },
                "required": ["path"]
            }
        }
    }
]

# --- Simulated tool implementations ---
def search_web(query: str) -> dict:
    """Simulates a web search. Replace with real search API (Tavily, SerpAPI, etc.)."""
    mock_results = {
        "python asyncio": {
            "summary": "asyncio is Python's built-in library for writing concurrent code using async/await syntax.",
            "source": "docs.python.org"
        },
        "example model input pricing": {
            "summary": "For this example, assume the model costs $2.00 per million input tokens.",
            "source": "mock pricing table"
        },
    }
    # Find a partial match
    for key, value in mock_results.items():
        if key.lower() in query.lower() or query.lower() in key.lower():
            return value
    return {"summary": f"No specific results found for '{query}'", "source": "mock"}

def calculate(expression: str) -> dict:
    """Safely evaluates a mathematical expression."""
    try:
        # Restrict to safe math operations
        allowed = set("0123456789+-*/()., **eE")
        if not all(c in allowed or c.isspace() for c in expression):
            return {"error": "Expression contains unsupported characters"}
        result = eval(expression, {"__builtins__": {}}, {})
        return {"expression": expression, "result": result}
    except Exception as e:
        return {"error": str(e)}

def read_file(path: str) -> dict:
    """Reads a local file."""
    try:
        with open(path, "r") as f:
            return {"path": path, "content": f.read()}
    except FileNotFoundError:
        return {"error": f"File not found: {path}"}
    except Exception as e:
        return {"error": str(e)}

AVAILABLE_FUNCTIONS = {
    "search_web": search_web,
    "calculate": calculate,
    "read_file": read_file,
}

# --- The agent loop ---
def run_agent(goal: str, max_iterations: int = 10) -> str:
    """
    Runs the observe-think-act loop until the model produces a final answer
    or the iteration limit is reached.
    """

    # prepare data:
    ## takes a goal and a maximum number of iterations

    ## initializes the message history with a system prompt and the user's goal
    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful research agent. You have access to tools for "
                "searching the web, performing calculations, and reading files. "
                "Use them as needed to complete the user's goal. "
                "When you have enough information to answer fully, respond with "
                "your final answer directly without calling any more tools."
            )
        },
        {
            "role": "user",
            "content": goal
        }
    ]

    iteration = 0

    # enter agent loop

    while iteration < max_iterations:
        iteration += 1
        print(f"\n--- Iteration {iteration} ---")

        # Think: ask the model what to do next
        response = client.chat.completions.create(
            model="gpt-5.4-mini",
            messages=messages,
            tools=tools,
            tool_choice="auto",
        )

        message = response.choices[0].message
        finish_reason = response.choices[0].finish_reason

        # Act: if no tool calls, the model has reached a final answer
        if finish_reason == "stop" or not message.tool_calls:
            print(f"Agent finished after {iteration} iteration(s).")
            return message.content

        # The model wants to call tools: execute them and observe the results
        messages.append(message)

        # execute each tool one by one, collects the results, 
        # and appends them to the message array
        for tool_call in message.tool_calls:
            func_name = tool_call.function.name
            func_args = json.loads(tool_call.function.arguments)

            print(f"  [Act] Calling {func_name}({func_args})")

            func = AVAILABLE_FUNCTIONS.get(func_name)
            if func:
                result = func(**func_args)
            else:
                result = {"error": f"Unknown function: {func_name}"}

            print(f"  [Observe] Result: {result}")

            # Add the observation back to the conversation
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(result)
            })

        # Then loop back to call the model again with the updated context

    # If we hit the iteration limit, ask the model for its best answer so far
    print(f"Warning: reached max iterations ({max_iterations}). Requesting final answer.")
    messages.append({
        "role": "user",
        "content": "You have reached the maximum number of iterations. "
                   "Please provide your best answer based on what you have found so far."
    })
    final_response = client.chat.completions.create(
        model="gpt-5.4-mini",
        messages=messages,
    )
    return final_response.choices[0].message.content

# --- Run the agent ---
if __name__ == "__main__":
    result = run_agent(
        "Look up the example model input pricing. If the input cost is per million tokens, "
        "how would I estimate the cost to process 500,000 input tokens?"
    )
    print(f"\nFinal Answer:\n{result}")