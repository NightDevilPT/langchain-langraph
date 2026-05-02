# agents/weather/tools/forecast.py
from langchain.tools import tool


@tool
def get_forecast(city: str, days: int = 3) -> str:
    """Get weather forecast for a given city for specified number of days."""
    forecast_data = {
        "San Francisco": ["Sunny, 68°F", "Cloudy, 65°F", "Foggy, 62°F"],
        "New York": ["Cloudy, 45°F", "Rainy, 42°F", "Snowy, 38°F"],
        "London": ["Rainy, 52°F", "Rainy, 50°F", "Cloudy, 48°F"],
    }
    
    if city in forecast_data:
        forecast = forecast_data[city][:days]
        return f"{days}-day forecast for {city}: {', '.join(forecast)}"
    return f"{days}-day forecast for {city}: Partly cloudy, around 60°F"