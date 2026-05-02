# agents/weather/tools/humidity.py
from langchain.tools import tool


@tool
def get_humidity(city: str) -> str:
    """Get humidity level for a given city."""
    humidity_data = {
        "San Francisco": "75%",
        "New York": "65%",
        "London": "85%",
        "Tokyo": "60%",
    }
    humidity = humidity_data.get(city, "70%")
    return f"Humidity in {city}: {humidity}"