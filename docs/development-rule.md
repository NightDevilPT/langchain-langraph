# LangChain-Langraph Rule Book

**Version:** 1.0 | **Stack:** Python · LangChain · LangGraph · Docker Model Runner

---

## Project Overview

Learning LangChain/LangGraph by building modular agents. LLM runs locally via Docker Model Runner at `http://localhost:12434/engines/v1` using `ai/qwen2.5`. Access it through `get_llm()` from `shared/llm.py` — never create ChatOpenAI directly.

---

## Folder Structure

```
langchain-langraph/
    agents/
        <agent_name>/
            agent.py          → Agent definition
            tools/
                __init__.py   → Exports all tools
                *.py          → One @tool per file
            prompts/
                __init__.py   → Exports all prompts
                *.py          → Prompt templates (system, user, few-shot)
    middleware/
        __init__.py           → Exports all middleware
        *.py                  → Middleware modules (add more anytime)
    shared/
        config.py             → Loads .env
        llm.py                → get_llm() factory
    run.py                    → CLI: setup, list, run agents
```

**Hard Rules:**

- Every agent is a folder under `agents/`
- Each agent has `tools/` and `prompts/` folders
- Tools and prompts are agent-specific, never shared across agents
- Middleware is reusable — import into any agent, add new hooks anytime
- `get_llm()` is the only way to get an LLM instance
- `@tool` decorator on every tool, with type hints and docstrings
- All prompt templates go in `prompts/` folder, one file per prompt type
- Import prompts in `agent.py` instead of hardcoding strings

---

## Agent Pattern

```python
from langchain.agents import create_agent
from shared.llm import get_llm
from tools import tool_1, tool_2
from prompts import system_prompt
from middleware import (
    log_before_agent, log_after_agent,
    log_before_model, log_after_model,
    log_wrap_model_call, log_wrap_tool_call,
)

agent = create_agent(
    model=get_llm(),
    tools=[tool_1, tool_2],
    system_prompt=system_prompt,
    middleware=[
        log_before_agent, log_after_agent,
        log_before_model, log_after_model,
        log_wrap_model_call, log_wrap_tool_call,
    ],
)

if __name__ == "__main__":
    result = agent.invoke(
        {"messages": [{"role": "user", "content": "Test query"}]}
    )
    print(result["messages"][-1].content)
```

---

## Prompts Pattern

```python
# agents/<name>/prompts/system.py
SYSTEM_PROMPT = """You are a helpful assistant.
Describe what you do and how to use your tools here."""

# agents/<name>/prompts/__init__.py
from .system import SYSTEM_PROMPT

__all__ = ["SYSTEM_PROMPT"]
```

For multiple prompts:

```python
# agents/<name>/prompts/__init__.py
from .system import SYSTEM_PROMPT
from .few_shot import FEW_SHOT_EXAMPLES
from .user_templates import QUERY_TEMPLATE

__all__ = ["SYSTEM_PROMPT", "FEW_SHOT_EXAMPLES", "QUERY_TEMPLATE"]
```

**Rules for prompts:**

- One file per prompt type (system, few-shot, user templates)
- Never hardcode long prompt strings in `agent.py`
- Always export prompts from `prompts/__init__.py`
- Prompts can use f-strings or `.format()` for dynamic parts

---

## Tool Pattern

```python
from langchain.tools import tool

@tool
def my_tool(param: str) -> str:
    """What this tool does. Args: param - description."""
    return f"Result: {param}"
```

---

## Middleware Pattern

| Decorator          | When            | Must do                          |
| ------------------ | --------------- | -------------------------------- |
| `@before_agent`    | Session starts  | Return `dict` or `None`          |
| `@after_agent`     | Session ends    | Return `dict` or `None`          |
| `@before_model`    | Before each LLM | Return `dict` or `None`          |
| `@after_model`     | After each LLM  | Return `dict` or `None`          |
| `@wrap_model_call` | Wraps LLM call  | Call `handler(request)` + return |
| `@wrap_tool_call`  | Wraps tool call | Call `handler(request)` + return |

**Add new middleware anytime** — create a `.py` file in `middleware/`, use the right decorator, export it in `__init__.py`, and add it to your agent's middleware list.

---

## 6 Middleware Hooks (Current)

| Hook                  | What It Does                         |
| --------------------- | ------------------------------------ |
| `log_before_agent`    | Resets counters, logs session start  |
| `log_after_agent`     | Prints total calls, tokens, duration |
| `log_before_model`    | Increments call count, logs request  |
| `log_after_model`     | Logs response, tracks token usage    |
| `log_wrap_model_call` | Times the model call, handles errors |
| `log_wrap_tool_call`  | Logs tool name/args/result, times it |

---

## Adding New Features Checklist

| Task           | Steps                                                                    |
| -------------- | ------------------------------------------------------------------------ |
| New Agent      | Create folder → `agent.py` → `tools/` → `prompts/` → test                |
| New Tool       | Create `.py` in `tools/` → `@tool` → add to `__init__.py` → add to agent |
| New Prompt     | Create `.py` in `prompts/` → add to `__init__.py` → import in `agent.py` |
| New Middleware | Create `.py` in `middleware/` → use decorator → export → add to agent    |
| Run Agent      | `python run.py <agent_name>`                                             |
