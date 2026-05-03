# agents/weather/agent.py
from langchain.agents import create_agent
from shared.llm import get_llm
from tools import get_weather, get_forecast, get_humidity
from middleware import (
    log_before_agent,
    log_after_agent,
    log_before_model,
    log_after_model,
    log_wrap_model_call,
    log_wrap_tool_call,
)

# Create the agent with all weather tools
agent = create_agent(
    model=get_llm(),
    tools=[get_weather, get_forecast, get_humidity],
    system_prompt="""You are a helpful weather assistant. 
    You can provide current weather, forecasts, and humidity information for various cities.
    Use the appropriate tool based on what the user asks for.""",
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
    print("\nWeather Agent with Multiple Tools\n" + "="*50)
    
    result = agent.invoke(
        {"messages": [{"role": "user", "content": "What's the weather in San Francisco and what will it be like for the next 2 days?"}]}
    )
    
    # Print final response
    if result and "messages" in result:
        last_message = result["messages"][-1]
        content = last_message.content if hasattr(last_message, 'content') else str(last_message)
        print(f"\n✅ Final Answer: {content}")