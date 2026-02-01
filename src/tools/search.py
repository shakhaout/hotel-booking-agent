import os
from serpapi import GoogleSearch
import json
from typing import List, Dict, Any

class HotelSearchTool:
    def __init__(self):
        self.api_key = os.getenv("SERPAPI_KEY")
        if not self.api_key:
            raise ValueError("SERPAPI_KEY environment variable not set")

    def search_hotels(self, query: str, check_in: str = None, check_out: str = None) -> List[Dict[str, Any]]:
        """
        Searches for hotels using SerpApi.
        
        Args:
            query: The location or hotel name to search for.
            check_in: Check-in date (YYYY-MM-DD).
            check_out: Check-out date (YYYY-MM-DD).
        """
        params = {
            "engine": "google_hotels",
            "q": query,
            "api_key": self.api_key,
            "hl": "en",
            "gl": "us",
            "currency": "JPY"
        }
        
        if check_in:
            params["check_in_date"] = check_in
        if check_out:
            params["check_out_date"] = check_out

        print(f"DEBUG: Searching hotels with query: {query}")
        search = GoogleSearch(params)
        results = search.get_dict()
        
        hotels = []
        if "properties" in results:
            for prop in results["properties"]:
                hotel = {
                    "name": prop.get("name"),
                    "description": prop.get("description", ""),
                    "price": prop.get("rate_per_night", {}).get("lowest", "N/A"),
                    "rating": prop.get("overall_rating"),
                    "reviews": prop.get("reviews"),
                    "link": prop.get("link"),
                    "amenities": prop.get("amenities", [])
                }
                hotels.append(hotel)
        
        return hotels[:10]  # Return top 10 results

if __name__ == "__main__":
    # Test
    try:
        tool = HotelSearchTool()
        results = tool.search_hotels("Hotels in New York", "2024-05-01", "2024-05-05")
        print(json.dumps(results, indent=2))
    except Exception as e:
        print(f"Error: {e}")
