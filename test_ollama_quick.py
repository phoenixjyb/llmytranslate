import asyncio
from src.services.ollama_client import OllamaClient

async def test_ollama():
    try:
        # Create a fresh client and force the base URL
        client = OllamaClient()
        client.base_url = "http://127.0.0.1:11434"  # Force correct URL
        print("Base URL:", client.base_url)
        result = await client.health_check()
        print("Ollama Health Check Result:", result)
        
        # Also test list_models
        models = await client.list_models()
        print("List Models Result:", models)
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    asyncio.run(test_ollama())
