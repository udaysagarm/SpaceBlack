import os
import httpx
import json
from langchain_core.tools import tool
from pydantic import BaseModel, Field

# Define the input schema
class OpenWeatherInput(BaseModel):
    city: str = Field(description="The city name to get the weather for (e.g., 'London', 'Tokyo').")

@tool(args_schema=OpenWeatherInput)
def get_current_weather(city: str) -> str:
    """
    Fetches the current weather for a given city using the OpenWeatherMap API.
    """
    # Load config to get API key
    config_path = "config.json"
    api_key = None
    
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
                api_key = config.get("skills", {}).get("openweather", {}).get("api_key")
        except Exception:
            pass
            
    # Fallback to env var
    if not api_key:
        api_key = os.environ.get("OPENWEATHER_API_KEY")

    if not api_key:
        return "Error: OpenWeather API key not found. Please configure it in the Skills settings."

    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"

    try:
        with httpx.Client() as client:
            response = client.get(url)
            response.raise_for_status()
            data = response.json()
            
            weather_desc = data["weather"][0]["description"]
            temp = data["main"]["temp"]
            feels_like = data["main"]["feels_like"]
            humidity = data["main"]["humidity"]
            
            return f"Weather in {city}: {weather_desc}, Temperature: {temp}°C, Feels like: {feels_like}°C, Humidity: {humidity}%"
            
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return f"Error: City '{city}' not found."
        elif e.response.status_code == 401:
            return "Error: Invalid OpenWeather API key."
        return f"Error fetching weather: {str(e)}"
    except Exception as e:
        return f"Error: {str(e)}"
