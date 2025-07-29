import requests

try:
    print("Testing requests library...")
    response = requests.get("http://127.0.0.1:11434/api/tags", timeout=5)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text[:200]}...")
except Exception as e:
    print(f"Error: {e}")
