from .tool import Tool
import requests
import json

class MapSearchTool(Tool):
    name = "map_search"
    description = "Search for a place on a map"
    params = {
        "place": {"description": "Place name to search for", "type": "string", "optional": "no"}
    }
    return_schema = {
        "type": "json",
        "columns": ["place_name", "latitude", "longitude"]
    }

    base_url = "https://photon.komoot.io/api/"

    def execute(self, params):
        place = params.get("place", "").lower()
        url = f"{self.base_url}?q={place}&limit=3"
        try:
            response = requests.get(url)
            return json.dumps(response.json())
        except:
            return "Error while loading MapSearch API"
