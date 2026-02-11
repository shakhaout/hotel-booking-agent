from src.server import search_hotels
import asyncio

print(f"Is callable? {callable(search_hotels)}")
print(f"Has run? {hasattr(search_hotels, 'run')}")

try:
    print("Trying .run(query='test')")
    # This might fail due to API key if it actually runs, but we want to see if it calls method
    res = search_hotels.run(query="test")
    print(f"Run result: {res}")
except Exception as e:
    print(f"Run error: {e}")

try:
    print("Trying .fn(query='test')")
    res = search_hotels.fn(query="test")
    print(f"Fn result: {res}")
except Exception as e:
    print(f"Fn error: {e}")
