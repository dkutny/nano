
from ..tool import Tool
import os
import pandas as pd


class HotelTool(Tool):
    name = "hotel"
    description = "Get hotel information for a given city"
    params = {
        "city": {"description": "City name to get hotel for", "type": "string", "optional": "no"},
        "type": {"description": "Type of hotel", "type": "string", "optional": "yes"},
        "stars": {"description": "Number of stars of the hotel", "type": "integer", "optional": "yes"}
    }
    return_schema = {"type": "csv", "columns": ["hotel_name", "city", "type","price", "availability"]}

    def execute(self, params):
        city = params.get("city", "")
        type = params.get("type", None)
        stars = params.get("stars", None)
        return self.get_hotel(city, type, stars)

    def get_hotel(self, city, type, stars):
        file_path = os.path.join(os.path.dirname(__file__), "hotel.csv")
        df = pd.read_csv(file_path)
        condition = df["city"] == city
        if type is not None:
            condition = condition & (df["type"] == type)
        if stars is not None:
            condition = condition & (df["stars"] == stars)
        df = df[condition]

        if len(df) == 0:
            return "No hotel found for the given city"
        else:
            return df.to_csv(index=False)
