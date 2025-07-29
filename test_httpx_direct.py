import asyncio
import httpx

async def test_httpx():
    try:
        headers = {
            "User-Agent": "curl/7.68.0",
            "Accept": "*/*",
            "Connection": "close"
        }
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(5.0),
            headers=headers,
            follow_redirects=True
        ) as client:
            print("Testing httpx with curl-like headers...")
            response = await client.get("http://127.0.0.1:11434/api/tags")
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_httpx())
