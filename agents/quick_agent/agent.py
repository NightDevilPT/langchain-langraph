# agents/01_quick_agent/agent.py
from langchain.agents import create_agent
from shared.llm import get_llm
from agents.quick_agent.tools.get_weather import get_weather
from middleware.logging_middleware import (
    log_before_agent,
    log_after_agent,
    log_before_model,
    log_after_model,
    log_wrap_model_call,
    log_wrap_tool_call,
)

# Create the agent
agent = create_agent(
    model=get_llm(),
    tools=[get_weather],
    system_prompt="You are a helpful assistant that provides weather information.",
    middleware=[
        log_before_agent,
        log_after_agent,
        log_before_model,
        log_after_model,
        log_wrap_model_call,
        log_wrap_tool_call,
    ],
)

# Run the agent
if __name__ == "__main__":
    result = agent.invoke(
        {"messages": [{"role": "user", "content": "What's the weather in San Francisco?"}]}
    )
    
    # Print the response
    if result and "messages" in result:
        last_message = result["messages"][-1]
        if hasattr(last_message, 'content'):
            print(last_message.content)
        elif hasattr(last_message, 'content_blocks'):
            print(last_message.content_blocks)