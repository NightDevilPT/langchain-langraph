# agents/weather/tools/weather.py
from langchain.tools import tool


@tool
def get_weather(city: str) -> str:
    """Get current weather for a given city."""
    weather_data = {
        "San Francisco": "Sunny, 68°F",
        "New York": "Cloudy, 45°F",
        "London": "Rainy, 52°F",
        "Tokyo": "Clear, 70°F",
        "Paris": "Partly cloudy, 60°F",
        "Sydney": "Sunny, 75°F",
    }
    return weather_data.get(city, f"Partly cloudy, 60°F in {city}")