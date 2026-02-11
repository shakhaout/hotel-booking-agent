from fastmcp import FastMCP
from src.tools.search import HotelSearchTool
from src.tools.booking import BookingTool
import json
import logging
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

# Configure logging
# logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("hotel-server")
logging.getLogger("docket").setLevel(logging.WARNING)
logging.getLogger("fastmcp").setLevel(logging.WARNING)

# Initialize FastMCP server
mcp = FastMCP("Hotel Agent")

# Initialize tools
search_tool = HotelSearchTool()
booking_tool = BookingTool()

@mcp.tool()
def search_hotels(query: str, check_in: str = "", check_out: str = "") -> str:
    """
    Searches for hotels using Google Hotels (via SerpApi).
    
    Args:
        query: Location or hotel name.
        check_in: Check-in date (YYYY-MM-DD).
        check_out: Check-out date (YYYY-MM-DD).
    """
    try:
        results = search_tool.search_hotels(query, check_in, check_out)
        return json.dumps(results)
    except Exception as e:
        logger.error(f"Error searching hotels: {e}")
        return json.dumps({"error": str(e)})

@mcp.tool()
def book_hotel(hotel_name: str, check_in: str, check_out: str) -> str:
    """
    Generates a booking link for a hotel.
    
    Args:
        hotel_name: Name of the hotel.
        check_in: Check-in date (YYYY-MM-DD).
        check_out: Check-out date (YYYY-MM-DD).
    """
    try:
        return booking_tool.generate_booking_link(hotel_name, check_in, check_out)
    except Exception as e:
        logger.error(f"Error generating booking link: {e}")
        return f"Error: {str(e)}"

if __name__ == "__main__":
    mcp.run()
