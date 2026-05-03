"""System Info Router - hardware or software"""
from typing import TypedDict, List, Annotated
import operator
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send
from langchain.agents import create_agent

from shared.llm import get_llm
from tools import get_cpu_info, get_memory_info, get_disk_info
from tools import get_os_info, get_python_packages, check_process
from prompts import HARDWARE_SYSTEM_PROMPT, SOFTWARE_SYSTEM_PROMPT
from prompts import CLASSIFIER_PROMPT, SYNTHESIZER_PROMPT

# ── Import Middleware ──────────────────────────────────────
from middleware import (
    log_before_agent,
    log_after_agent,
    log_before_model,
    log_after_model,
    log_wrap_model_call,
    log_wrap_tool_call,
)


class RouterState(TypedDict):
    query: str
    classification: str
    results: Annotated[List[dict], operator.add]
    final_answer: str


# Create agents WITH middleware
hardware_agent = create_agent(
    model=get_llm(),
    tools=[get_cpu_info, get_memory_info, get_disk_info],
    system_prompt=HARDWARE_SYSTEM_PROMPT,
    # middleware=[  # ← ADD MIDDLEWARE HERE
    #     log_before_agent,
    #     log_after_agent,
    #     log_before_model,
    #     log_after_model,
    #     log_wrap_model_call,
    #     log_wrap_tool_call,
    # ],
)

software_agent = create_agent(
    model=get_llm(),
    tools=[get_os_info, get_python_packages, check_process],
    system_prompt=SOFTWARE_SYSTEM_PROMPT,
    # middleware=[  # ← ADD MIDDLEWARE HERE
    #     log_before_agent,
    #     log_after_agent,
    #     log_before_model,
    #     log_after_model,
    #     log_wrap_model_call,
    #     log_wrap_tool_call,
    # ],
)


def classify_query(state: RouterState) -> dict:
    """Route to hardware or software"""
    llm = get_llm()
    
    result = llm.invoke([
        {"role": "system", "content": CLASSIFIER_PROMPT},
        {"role": "user", "content": state["query"]}
    ])
    
    classification = result.content.strip().lower()
    classification = "hardware" if "hardware" in classification else "software"
    state["classification"] = classification
    
    return state


def route_to_agent(state: RouterState) -> List[Send]:
    """Send to one agent based on classification"""
    return state["classification"]


def query_hardware(state: dict) -> dict:
    """Run hardware agent"""
    result = hardware_agent.invoke(
        {"messages": [{"role": "user", "content": state["query"]}]}
    )
    return {"results": [{"source": "hardware", "result": result["messages"][-1].content}]}


def query_software(state: dict) -> dict:
    """Run software agent"""
    result = software_agent.invoke(
        {"messages": [{"role": "user", "content": state["query"]}]}
    )
    return {"results": [{"source": "software", "result": result["messages"][-1].content}]}


def synthesize(state: RouterState) -> dict:
    """Combine results"""
    if not state["results"]:
        return {"final_answer": "No results found"}
    
    formatted = "\n".join([r["result"] for r in state["results"]])
    prompt = SYNTHESIZER_PROMPT.format(query=state["query"], results=formatted)
    
    llm = get_llm()
    response = llm.invoke(prompt)
    
    return {"final_answer": response.content}


# Build workflow
workflow = StateGraph(RouterState)

workflow.add_node("classify", classify_query)
workflow.add_node("queryHardware", query_hardware)
workflow.add_node("querySoftware", query_software)
workflow.add_node("synthesize", synthesize)

workflow.add_edge(START, "classify")
workflow.add_conditional_edges("classify", route_to_agent, {
	"hardware": "queryHardware",
	"software": "querySoftware"
})
workflow.add_edge("queryHardware", "synthesize")
workflow.add_edge("querySoftware", "synthesize")
workflow.add_edge("synthesize", END)

router = workflow.compile()
# workflow.draw("./it_asset_router_workflow.png")


# ── Test Invocation ────────────────────────────────────────

if __name__ == "__main__":
    # Test 1: Hardware query
    result = router.invoke({
        "query": "Show me CPU and memory information"
    })
    
    print("=" * 60)
    print("ORIGINAL QUERY:", result["query"])
    print("\nCLASSIFICATION:", result["classification"])
    print("\n" + "=" * 60)
    print("FINAL ANSWER:")
    print(result["final_answer"])
    print("=" * 60)
    
    print("\n\n")
    
    # Test 2: Software query
    result = router.invoke({
        "query": "What OS am I running and what Python packages are installed?"
    })
    
    print("=" * 60)
    print("ORIGINAL QUERY:", result["query"])
    print("\nCLASSIFICATION:", result["classification"])
    print("\n" + "=" * 60)
    print("FINAL ANSWER:")
    print(result["final_answer"])
    print("=" * 60)