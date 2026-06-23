from dotenv import load_dotenv
from openai import OpenAI
import json
import requests
import os
load_dotenv()
client = OpenAI(
    api_key='GROK_API',
    base_url="https://api.groq.com/openai/v1"
)

# ── Tools ─────────────────────────────────────────────────────────────────────

def get_weather(city: str):
    url = f"https://wttr.in/{city}?format=%C+%t"
    response = requests.get(url)
    if response.status_code == 200:
        return f"The weather in {city} is {response.text}."
    return "Something went wrong fetching weather."

def run_command(cmd: str):
    import subprocess
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        return result.stdout or result.stderr or "Command executed with no output."
    except Exception as e:
        return f"Error running command: {e}"

def get_stock_price(symbol: str):
    api_key = "STOCK_API"
    url = (
        f"https://www.alphavantage.co/query?"
        f"function=GLOBAL_QUOTE&symbol={symbol}&apikey={api_key}"
    )
    response = requests.get(url)
    data = response.json()
    if "Global Quote" not in data or not data["Global Quote"]:
        return f"Could not fetch stock data for {symbol}. Check the symbol or API key."
    quote = data["Global Quote"]
    return {"symbol": quote["01. symbol"], "price": quote["05. price"]}

available_tools = {
    "get_weather": get_weather,
    "run_command": run_command,
    "get_stock_price": get_stock_price,
}

SYSTEM_PROMPT = """
    You are a helpful AI Assistant specialized in resolving user queries.
    You work on start, plan, action, observe mode.

    For the given user query and available tools, plan the step by step execution, based on the planning,
    select the relevant tool from the available tools, and based on the tool selection you perform an action to call the tool.

    Wait for the observation and based on the observation from the tool call resolve the user query.

    Rules:
    - Follow the Output JSON Format.
    - Always perform one step at a time and wait for next input
    - Carefully analyse the user query
    - Never use run_command as a fallback for get_weather or get_stock_price.
    - Use run_command only when the user explicitly asks to execute a system command.

    Output JSON Format:
    {
        "step": "string",
        "content": "string",
        "function": "The name of function if the step is action",
        "input": "The input parameter for the function"
    }

    Available Tools:
    - "get_weather": Takes a city name as input and returns the current weather.
    - "run_command": Takes a system command as a string and executes it.
    - "get_stock_price": Takes a stock symbol (e.g. AAPL, TSLA, MSFT, IBM) and returns the latest price.
"""

# ── Agent runner (yields steps for Streamlit to display live) ─────────────────

def run_agent(query: str, messages: list):
    """
    Takes a query and existing message history.
    Yields dicts describing each step so Streamlit can display them live.
    Returns updated messages list via the last yielded item.
    """
    messages.append({"role": "user", "content": query})

    while True:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            response_format={"type": "json_object"},
            messages=messages
        )

        raw = response.choices[0].message.content
        messages.append({"role": "assistant", "content": raw})
        parsed = json.loads(raw)
        step = parsed.get("step")

        if step == "plan":
            yield {"type": "plan", "content": parsed.get("content", "")}
            continue

        if step == "action":
            tool_name  = parsed.get("function")
            tool_input = parsed.get("input")
            yield {"type": "action", "tool": tool_name, "input": tool_input}

            if tool_name in available_tools:
                output = available_tools[tool_name](tool_input)
            else:
                output = f"Unknown tool: {tool_name}"

            yield {"type": "observe", "output": output}
            messages.append({
                "role": "user",
                "content": json.dumps({"step": "observe", "output": output})
            })
            continue

        if step == "output":
            yield {"type": "output", "content": parsed.get("content", ""), "messages": messages}
            break
if __name__ == "__main__":
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    while True:
        query = input("You: ")   # 👈 THIS is what you are missing

        if query.lower() in ["exit", "quit"]:
            print("Exiting...")
            break

        for step in run_agent(query, messages):
            if step["type"] == "plan":
                print("🧠 Plan:", step["content"])

            elif step["type"] == "action":
                print(f"⚙️ Action: {step['tool']}({step['input']})")

            elif step["type"] == "observe":
                print("👀 Observation:", step["output"])

            elif step["type"] == "output":
                print("✅ Final Answer:", step["content"])
                messages = step["messages"]  # keep memory        
