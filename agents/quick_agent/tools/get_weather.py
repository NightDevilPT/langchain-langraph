# agents/01_quick_agent/tools/get_weather.py
def get_weather(city: str) -> str:
    """Get weather for a given city."""
    weather_data = {
        "San Francisco": "Sunny, 68°F",
        "New York": "Cloudy, 45°F",
        "London": "Rainy, 52°F",
        "Tokyo": "Clear, 70°F",
    }
    return weather_data.get(city, f"Partly cloudy, 60°F in {city}")