from .tool import Tool
import requests
import json
import re


class WikiTool(Tool):
    name = "wiki"
    description = "Search Wikipedia for information about a topic"
    params = {
        "query": {
            "description":  "Search term to look up. Query must be precise and specific, i.e. 'The Mona Lisa' or 'The Mona Lisa'",
            "type": "string", 
            "optional": "no"
        }
    }
    return_schema = {
        "type": "json",
        "columns": ["label", "wikipedia_url", "description", "categories"]
    }

    base_url = "https://lookup.dbpedia.org/api/search"

    def execute(self, params):
        query = params.get("query")

        if not query:
            return "Error: Query parameter is required"

        try:
            response = requests.get(f"{self.base_url}?query={query}")
            if response.status_code != 200:
                return f"Error: API request failed with status {response.status_code}"

            xml_text = response.text
            results = []
            label_matches = re.findall(r"<Label>(.*?)</Label>", xml_text)[:3]
            uri_matches = re.findall(r"<URI>(.*?)</URI>", xml_text)[:3]
            desc_matches = re.findall(r"<Description>(.*?)</Description>", xml_text)[:3]
            category_sections = re.findall(r"<Categories>(.*?)</Categories>", xml_text)[:3]
            all_categories = []
            for section in category_sections:
                categories = re.findall(r"<Label>(.*?)</Label>", section)
                all_categories.append(categories)

            for i in range(min(3, len(label_matches))):
                wiki_url = uri_matches[i].replace("dbpedia.org/resource", "wikipedia.org/wiki")
                
                result = {
                    "label": label_matches[i],
                    "wikipedia_url": wiki_url,
                    "description": desc_matches[i] if i < len(desc_matches) else "",
                    "categories": all_categories[i] if i < len(all_categories) else []
                }
                results.append(result)

            return json.dumps({"results": results})
            
        except Exception as e:
            return f"Error while querying Wikipedia: {str(e)}"
