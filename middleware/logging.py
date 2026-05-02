import time
import json
import threading
from datetime import datetime
from typing import Any, Callable, Optional

from langchain.agents.middleware import (
    before_agent,
    after_agent,
    before_model,
    after_model,
    wrap_model_call,
    wrap_tool_call,
    AgentState,
    ModelRequest,
    ModelResponse,
)
from langchain.tools.tool_node import ToolCallRequest
from langchain.messages import ToolMessage
from langgraph.types import Command
from langgraph.runtime import Runtime


# ── Global session state ──────────────────────────────────────────────────────
model_call_count    = 0
tool_call_count     = 0
session_start_time  = None
total_input_tokens  = 0
total_output_tokens = 0
total_tokens        = 0

# Lock prevents parallel tool calls from interleaving their output
_print_lock = threading.Lock()


# ── ANSI colours ──────────────────────────────────────────────────────────────
class Colors:
    PURPLE = "\033[95m"
    BLUE   = "\033[94m"
    CYAN   = "\033[96m"
    GREEN  = "\033[92m"
    YELLOW = "\033[93m"
    RED    = "\033[91m"
    ORANGE = "\033[38;5;208m"
    BOLD   = "\033[1m"
    DIM    = "\033[2m"
    RESET  = "\033[0m"


# ── Helpers ───────────────────────────────────────────────────────────────────
def _divider(phase: str, color: str = Colors.CYAN) -> None:
    print(f"\n{color}{'=' * 60}{Colors.RESET}")
    print(f"{color}{Colors.BOLD}  {phase}{Colors.RESET}")
    print(f"{color}{'=' * 60}{Colors.RESET}")


def _log_table(rows: list, title: str = None, color: str = Colors.CYAN) -> None:
    if title:
        print(f"\n{color}{Colors.BOLD}{title}{Colors.RESET}")
        print(f"{color}{'-' * 50}{Colors.RESET}")
    for row in rows:
        if isinstance(row, tuple):
            key, value = row
            print(f"{color}{key:<25}{Colors.RESET}{value}")
        else:
            print(f"{color}{row}{Colors.RESET}")
    print(f"{color}{'-' * 50}{Colors.RESET}")


def _get_user_input(state: AgentState) -> str:
    for msg in reversed(state.get("messages", [])):
        if hasattr(msg, "type") and msg.type == "human":
            content = msg.content
            return content[:200] + "..." if len(content) > 200 else content
    return "N/A"


def _collect_tokens(last_msg) -> tuple[int, int]:
    input_tokens  = 0
    output_tokens = 0
    if not last_msg:
        return input_tokens, output_tokens
    meta = getattr(last_msg, "response_metadata", {}) or {}
    for key in ("token_usage", "usage"):
        if key in meta:
            usage         = meta[key]
            input_tokens  = usage.get("prompt_tokens", 0)
            output_tokens = usage.get("completion_tokens", 0)
            break
    return input_tokens, output_tokens


# ── Middleware hooks ──────────────────────────────────────────────────────────
@before_agent
def log_before_agent(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    global session_start_time, model_call_count, tool_call_count
    global total_input_tokens, total_output_tokens, total_tokens

    session_start_time  = time.time()
    model_call_count    = 0
    tool_call_count     = 0
    total_input_tokens  = 0
    total_output_tokens = 0
    total_tokens        = 0

    _divider("BEFORE_AGENT", Colors.PURPLE)
    _log_table(
        [
            ("Event:",            "Agent Session Started"),
            ("Timestamp:",        datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            ("Session ID:",       str(id(state))[:8]),
            ("Initial Messages:", str(len(state.get("messages", [])))),
        ],
        "SESSION INITIALIZATION",
        Colors.PURPLE,
    )
    return None


@before_model
def log_before_model(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    global model_call_count
    model_call_count += 1

    _divider("BEFORE_MODEL", Colors.BLUE)
    _log_table(
        [
            ("Call Number:",    f"#{model_call_count}"),
            ("Timestamp:",      datetime.now().strftime("%H:%M:%S.%f")[:-3]),
            ("Total Messages:", str(len(state.get("messages", [])))),
            ("User Input:",     _get_user_input(state)),
        ],
        "MODEL REQUEST",
        Colors.BLUE,
    )
    return None


@wrap_model_call
def log_wrap_model_call(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse],
) -> ModelResponse:
    _divider("WRAP_MODEL_CALL", Colors.CYAN)

    start = time.time()
    rows  = [
        ("Messages in Request:", str(len(request.messages))),
        ("Start Time:",          datetime.now().strftime("%H:%M:%S.%f")[:-3]),
    ]

    try:
        response = handler(request)
        rows += [
            ("Execution Time:", f"{time.time() - start:.3f} seconds"),
            ("Status:",         "SUCCESS"),
        ]
        _log_table(rows, "MODEL WRAPPER", Colors.CYAN)
        return response
    except Exception as e:
        rows += [("Status:", "FAILED"), ("Error:", str(e))]
        _log_table(rows, "MODEL WRAPPER", Colors.RED)
        raise


@after_model
def log_after_model(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    global total_input_tokens, total_output_tokens, total_tokens

    _divider("AFTER_MODEL", Colors.BLUE)

    messages = state.get("messages", [])
    last_msg = messages[-1] if messages else None

    # accumulate tokens for summary
    inp, out = _collect_tokens(last_msg)
    total_input_tokens  += inp
    total_output_tokens += out
    total_tokens         = total_input_tokens + total_output_tokens

    rows = [
        ("Call Number:", f"#{model_call_count}"),
        ("Timestamp:",   datetime.now().strftime("%H:%M:%S.%f")[:-3]),
    ]

    if last_msg:
        if getattr(last_msg, "content", None):
            content = last_msg.content
            rows.append(("\nAI Response:", f"\n{content[:300]}"))
        elif getattr(last_msg, "tool_calls", None):
            names = [tc.get("name", "unknown") for tc in last_msg.tool_calls]
            rows.append(("AI Decision:", f"Calling tool(s): {', '.join(names)}"))

    _log_table(rows, "MODEL RESPONSE", Colors.BLUE)
    return None


@wrap_tool_call
def log_wrap_tool_call(
    request: ToolCallRequest,
    handler: Callable[[ToolCallRequest], ToolMessage | Command],
) -> ToolMessage | Command:
    global tool_call_count

    tool_name = request.tool_call.get("name", "unknown")
    tool_args = request.tool_call.get("args", {})

    # ── Acquire lock so parallel tools never interleave output ────────────────
    with _print_lock:
        tool_call_count += 1
        current_call = tool_call_count

        _divider("WRAP_TOOL_CALL", Colors.ORANGE)

        start = time.time()
        rows  = [
            ("Call Number:", f"#{current_call}"),
            ("Tool Name:",   tool_name),
            ("Arguments:",   json.dumps(tool_args, ensure_ascii=False)[:200]),
            ("Start Time:",  datetime.now().strftime("%H:%M:%S.%f")[:-3]),
        ]

        try:
            result   = handler(request)
            duration = time.time() - start

            rows.append(("Execution Time:", f"{duration:.3f} seconds"))

            if isinstance(result, ToolMessage):
                output = str(result.content)
                rows += [
                    ("Output:",  output[:200] + ("..." if len(output) > 200 else "")),
                    ("Status:",  "SUCCESS"),
                ]
            else:
                rows.append(("Status:", "SUCCESS (Command)"))

            _log_table(rows, f"TOOL EXECUTION  [{tool_name}]", Colors.ORANGE)
            return result

        except Exception as e:
            rows += [("Status:", "FAILED"), ("Error:", str(e))]
            _log_table(rows, f"TOOL EXECUTION  [{tool_name}]", Colors.RED)
            raise


@after_agent
def log_after_agent(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    duration = time.time() - session_start_time if session_start_time else 0

    _divider("AFTER_AGENT", Colors.PURPLE)

    rows = [
        ("Session Duration:",    f"{duration:.2f} seconds"),
        ("Total Model Calls:",   str(model_call_count)),
        ("Total Tool Calls:",    str(tool_call_count)),
        ("Total Input Tokens:",  str(total_input_tokens)),
        ("Total Output Tokens:", str(total_output_tokens)),
        ("Total Tokens Used:",   str(total_tokens)),
    ]

    if duration > 0 and total_tokens > 0:
        rows.append(("Average Speed:", f"{total_tokens / duration:.1f} tokens/sec"))

    _log_table(rows, "SESSION SUMMARY", Colors.PURPLE)
    return None