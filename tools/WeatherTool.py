from .tool import Tool
import requests
import json
import logging as lg
from datetime import datetime, timezone


class WeatherTool(Tool):
    name = "weather"
    description = "Get the weather for a given location"
    params = {
        "lat": {"description": "Latitude", "type": "number", "optional": "no"},
        "lon": {"description": "Longitude", "type": "number", "optional": "no"},
        "date": {"description": "Date in YYYY-MM-DD format. If not provided, the current date is used.", "type": "string", "optional": ""}
    }
    return_schema = {
        "type": "json",
        "columns": ["timestamp", "temperature", "precipitation", "condition"]
    }

    base_url = "https://api.brightsky.dev/weather"

    def execute(self, params):
        lat = params.get("lat")
        lon = params.get("lon")
        
        if not lat or not lon:
            return "Error: Latitude and Longitude are required"

        date = params.get("date", "")

        if not date:
            date = datetime.now().strftime("%Y-%m-%d")

        url = f"{self.base_url}?lat={lat}&lon={lon}"

        if date:
            url += f"&date={date}"

        try:    
            response = requests.get(url)
            data = response.json()
            
            # Find entry closest to current time
            current_time = datetime.now(timezone.utc)  # Get UTC time
            weather_entries = data.get("weather", [])
            
            if not weather_entries:
                return "No weather data available"
                
            closest_entry = min(
                weather_entries,
                key=lambda x: abs(datetime.fromisoformat(x["timestamp"]) - current_time)
            )

            lg.debug(f"Weather data: {closest_entry}")
            
            return json.dumps({"weather": [closest_entry]})
        except Exception as e:
            return f"Error while loading Weather API: {str(e)}"
