from ..tool import Tool
import os
import pandas as pd


class SightseeingTool(Tool):
    name = "sightseeing"
    description = "Get sightseeing information for a given city"
    params = {
        "city": {"description": "City name to get sightseeing for", "type": "string", "optional": "no"},
        "type": {"description": "Type of sightseeing", "type": "string", "optional": "yes"}
    }
    return_schema = {"type": "csv", "columns": ["sightseeing_name", "city", "type","price", "availability"]}

    def execute(self, params):
        city = params.get("city", "")
        type = params.get("type", None)
        return self.get_sightseeing(city, type)

    def get_sightseeing(self, city, type):
        file_path = os.path.join(os.path.dirname(__file__), "sightseeing.csv")
        df = pd.read_csv(file_path)
        df = df[df["City"] == city]

        if len(df) == 0:
            return "No sightseeing found for the given city"
        else:
            return df.to_csv(index=False)
