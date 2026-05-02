# middleware/logging_middleware.py
import time
import json
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


model_call_count = 0
tool_call_count = 0
session_start_time = None
total_input_tokens = 0
total_output_tokens = 0
total_tokens = 0


# ANSI color codes
class Colors:
    PURPLE = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ORANGE = '\033[38;5;208m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    RESET = '\033[0m'


def _log_table(rows: list, title: str = None, color: str = Colors.CYAN):
    """Print logs in table format"""
    if title:
        print(f"\n{color}{Colors.BOLD}{title}{Colors.RESET}")
        print(f"{color}{'-' * 50}{Colors.RESET}")
    
    for row in rows:
        if isinstance(row, tuple):
            key, value = row
            print(f"{color}{key:<20}{Colors.RESET} {value}")
        else:
            print(f"{color}{row}{Colors.RESET}")
    
    print(f"{color}{'-' * 50}{Colors.RESET}")


def _divider(phase: str, color: str = Colors.CYAN):
    print(f"\n{color}{'='*60}{Colors.RESET}")
    print(f"{color}{Colors.BOLD}  {phase}{Colors.RESET}")
    print(f"{color}{'='*60}{Colors.RESET}")


def _extract_token_usage(response: Optional[ModelResponse]) -> tuple:
    """Extract token usage from model response if available"""
    input_tokens = 0
    output_tokens = 0
    
    if response and hasattr(response, 'usage_metadata') and response.usage_metadata:
        usage = response.usage_metadata
        input_tokens = usage.get('input_tokens', 0)
        output_tokens = usage.get('output_tokens', 0)
    elif response and hasattr(response, 'response_metadata') and response.response_metadata:
        metadata = response.response_metadata
        if 'token_usage' in metadata:
            usage = metadata['token_usage']
            input_tokens = usage.get('prompt_tokens', 0)
            output_tokens = usage.get('completion_tokens', 0)
        elif 'usage' in metadata:
            usage = metadata['usage']
            input_tokens = usage.get('prompt_tokens', 0)
            output_tokens = usage.get('completion_tokens', 0)
    
    return input_tokens, output_tokens


@before_agent
def log_before_agent(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    global session_start_time, model_call_count, tool_call_count, total_input_tokens, total_output_tokens, total_tokens
    session_start_time = time.time()
    model_call_count = 0
    tool_call_count = 0
    total_input_tokens = 0
    total_output_tokens = 0
    total_tokens = 0
    
    _divider("BEFORE_AGENT", Colors.PURPLE)
    
    rows = [
        ("Event:", "Agent Session Started"),
        ("Timestamp:", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        ("Session ID:", str(id(state))[:8]),
        ("Initial Messages:", str(len(state.get("messages", [])))),
    ]
    _log_table(rows, "SESSION INITIALIZATION", Colors.PURPLE)
    
    return None


@before_model
def log_before_model(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    global model_call_count
    model_call_count += 1
    
    _divider("BEFORE_MODEL", Colors.BLUE)
    
    rows = [
        ("Call Number:", f"#{model_call_count}"),
        ("Timestamp:", datetime.now().strftime("%H:%M:%S.%f")[:-3]),
        ("Total Messages:", str(len(state.get("messages", [])))),
    ]
    
    # Get user input
    messages = state.get("messages", [])
    for msg in reversed(messages):
        if hasattr(msg, 'type') and msg.type == "human":
            content = msg.content[:200] if len(msg.content) > 200 else msg.content
            rows.append(("User Input:", content))
            break
    
    _log_table(rows, "MODEL REQUEST", Colors.BLUE)
    
    return None


@after_model
def log_after_model(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    global total_input_tokens, total_output_tokens, total_tokens
    
    _divider("AFTER_MODEL", Colors.BLUE)
    
    messages = state.get("messages", [])
    last_msg = messages[-1] if messages else None
    
    rows = [
        ("Call Number:", f"#{model_call_count}"),
        ("Timestamp:", datetime.now().strftime("%H:%M:%S.%f")[:-3]),
    ]
    
    # Collect token usage for summary (but don't display)
    input_tokens = 0
    output_tokens = 0
    
    if last_msg and hasattr(last_msg, 'response_metadata'):
        metadata = last_msg.response_metadata
        if 'token_usage' in metadata:
            input_tokens = metadata['token_usage'].get('prompt_tokens', 0)
            output_tokens = metadata['token_usage'].get('completion_tokens', 0)
        elif 'usage' in metadata:
            input_tokens = metadata['usage'].get('prompt_tokens', 0)
            output_tokens = metadata['usage'].get('completion_tokens', 0)
    
    if input_tokens or output_tokens:
        total_input_tokens += input_tokens
        total_output_tokens += output_tokens
        total_tokens = total_input_tokens + total_output_tokens
    
    if last_msg and hasattr(last_msg, 'content') and last_msg.content:
        content = last_msg.content[:300] if len(last_msg.content) > 300 else last_msg.content
        rows.append(("\nAI Response:", f"\n{content}"))
    elif last_msg and hasattr(last_msg, 'tool_calls') and last_msg.tool_calls:
        # Extract tool names
        tool_names = [tc.get('name', 'unknown') for tc in last_msg.tool_calls]
        tools_text = ", ".join(tool_names)
        rows.append(("AI Decision:", f"Calling tool(s): {tools_text}"))
    
    _log_table(rows, "MODEL RESPONSE", Colors.BLUE)
    
    return None


@after_agent
def log_after_agent(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    global session_start_time, model_call_count, tool_call_count, total_input_tokens, total_output_tokens, total_tokens
    duration = time.time() - session_start_time if session_start_time else 0
    
    _divider("AFTER_AGENT", Colors.PURPLE)
    
    rows = [
        ("Session Duration:", f"{duration:.2f} seconds"),
        ("Total Model Calls:", str(model_call_count)),
        ("Total Tool Calls:", str(tool_call_count)),
        ("Total Input Tokens:", str(total_input_tokens)),
        ("Total Output Tokens:", str(total_output_tokens)),
        ("Total Tokens Used:", str(total_tokens)),
    ]
    
    if duration > 0 and total_tokens > 0:
        rows.append(("Average Speed:", f"{total_tokens/duration:.1f} tokens/sec"))
    
    _log_table(rows, "SESSION SUMMARY", Colors.PURPLE)
    
    return None


@wrap_model_call
def log_wrap_model_call(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse],
) -> ModelResponse:
    _divider("WRAP_MODEL_CALL", Colors.CYAN)
    
    rows = [
        ("Messages in Request:", str(len(request.messages))),
        ("Start Time:", datetime.now().strftime("%H:%M:%S.%f")[:-3]),
    ]
    
    start = time.time()
    try:
        response = handler(request)
        duration = time.time() - start
        
        rows.append(("Execution Time:", f"{duration:.3f} seconds"))
        rows.append(("Status:", "SUCCESS"))
        _log_table(rows, "MODEL WRAPPER", Colors.CYAN)
        
        return response
    except Exception as e:
        rows.append(("Status:", "FAILED"))
        rows.append(("Error:", str(e)))
        _log_table(rows, "MODEL WRAPPER", Colors.RED)
        raise


@wrap_tool_call
def log_wrap_tool_call(
    request: ToolCallRequest,
    handler: Callable[[ToolCallRequest], ToolMessage | Command],
) -> ToolMessage | Command:
    global tool_call_count
    tool_call_count += 1
    
    _divider("WRAP_TOOL_CALL", Colors.ORANGE)
    
    tool_name = request.tool_call.get('name', 'unknown')
    tool_args = request.tool_call.get('args', {})
    
    rows = [
        ("Call Number:", f"#{tool_call_count}"),
        ("Tool Name:", tool_name),
        ("Arguments:", json.dumps(tool_args)[:150]),
        ("Start Time:", datetime.now().strftime("%H:%M:%S.%f")[:-3]),
    ]
    
    start = time.time()
    try:
        result = handler(request)
        duration = time.time() - start
        
        rows.append(("Execution Time:", f"{duration:.3f} seconds"))
        
        if isinstance(result, ToolMessage):
            output = str(result.content)[:150] if len(str(result.content)) > 150 else str(result.content)
            rows.append(("Output:", output))
            rows.append(("Status:", "SUCCESS"))
            _log_table(rows, "TOOL EXECUTION", Colors.ORANGE)
        else:
            rows.append(("Status:", "SUCCESS (Command)"))
            _log_table(rows, "TOOL EXECUTION", Colors.ORANGE)
        
        return result
    except Exception as e:
        rows.append(("Status:", "FAILED"))
        rows.append(("Error:", str(e)))
        _log_table(rows, "TOOL EXECUTION", Colors.RED)
        raise