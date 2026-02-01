import urllib.parse

class BookingTool:
    def generate_booking_link(self, hotel_name: str, check_in: str, check_out: str) -> str:
        """
        Generates a direct booking link (Mock or Deep Link).
        Since we can't scrape the dynamic booking token easily without a session,
        we will generate a Google Hotel Search deep link for that specific hotel and output it.
        """
        base_url = "https://www.google.com/travel/hotels"
        query_params = {
            "q": hotel_name,
            "dpr": 1
        }
        # Note: True deep linking to the checkout page is complex and often requires affiliate tokens.
        # We will point the user to the specific hotel's date selection page on Google Travel.
        
        encoded_query = urllib.parse.urlencode(query_params)
        return f"{base_url}?{encoded_query}"

if __name__ == "__main__":
    tool = BookingTool()
    link = tool.generate_booking_link("Grand Plaza Hotel", "2024-05-01", "2024-05-05")
    print(f"Booking Link: {link}")
