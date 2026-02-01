from fastmcp import FastMCP
from src.tools.search import HotelSearchTool
from src.tools.booking import BookingTool
import json
from dotenv import load_dotenv

load_dotenv()

# Initialize FastMCP server
mcp = FastMCP("Hotel Agent")

# Initialize tools
search_tool = HotelSearchTool()
booking_tool = BookingTool()

@mcp.tool()
def search_hotels(query: str, check_in: str = None, check_out: str = None) -> str:
    """
    Searches for hotels using Google Hotels (via SerpApi).
    
    Args:
        query: Location or hotel name.
        check_in: Check-in date (YYYY-MM-DD).
        check_out: Check-out date (YYYY-MM-DD).
    """
    results = search_tool.search_hotels(query, check_in, check_out)
    return json.dumps(results)

@mcp.tool()
def book_hotel(hotel_name: str, check_in: str, check_out: str) -> str:
    """
    Generates a booking link for a hotel.
    
    Args:
        hotel_name: Name of the hotel.
        check_in: Check-in date (YYYY-MM-DD).
        check_out: Check-out date (YYYY-MM-DD).
    """
    return booking_tool.generate_booking_link(hotel_name, check_in, check_out)

if __name__ == "__main__":
    mcp.run()
