import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("GOOGLE_API_KEY not set")
    exit(1)

client = genai.Client(api_key=api_key)

print("Listing models...")
try:
    for model in client.models.list():
        print(f"Model: {model.name}")
        print(f"  DisplayName: {model.display_name}")
        print(f"  SupportedActions: {model.supported_actions}")
except Exception as e:
    print(f"Error listing models: {e}")
