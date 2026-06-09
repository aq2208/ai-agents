import anthropic
import json

client = anthropic.Anthropic()

# Your data source as a tool function
def fetch_tickets(limit: int = 10) -> list:
    # Hackathon version: return mock data from a JSON file
    return [
        {"id": 1, "title": "Login fails on iOS", "domain": "auth", "count": 42},
        {"id": 2, "title": "Payment timeout error", "domain": "payment", "count": 18},
    ]

# Tell Claude this tool exists
tools = [{
    "name": "fetch_tickets",
    "description": "Fetch recent user complaints from the ticket system",
    "input_schema": {
        "type": "object",
        "properties": {
            "limit": {"type": "integer", "description": "How many tickets to return"}
        },
        "required": []
    }
}]

messages = [{"role": "user", "content": "Analyze today's tickets and summarize issues by domain"}]

# Agent loop
while True:
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        system="You are a data analysis agent. Use tools to gather data, then write a structured summary.",
        tools=tools,
        messages=messages
    )

    if response.stop_reason == "end_turn":
        # Final answer — print the report
        print(response.content[0].text)
        break

    # Claude wants to call a tool
    for block in response.content:
        if block.type == "tool_use":
            result = fetch_tickets(**block.input)  # execute the function
            # Feed result back into the conversation
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": [{
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": json.dumps(result)
            }]})
            break