#!/usr/bin/env python3
"""
LLM Translation Service - Network enabled version
Accessible from remote networks for translation services
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import httpx
import asyncio
from typing import Optional
import json

# Create FastAPI app for network access
app = FastAPI(
    title="LLM Translation Service",
    description="Remote translation service using Ollama LLM",
    version="1.0.0"
)

# Request/Response models
class TranslationRequest(BaseModel):
    text: str
    source_language: Optional[str] = "auto"
    target_language: str
    model: Optional[str] = "llama3.1:8b"

class TranslationResponse(BaseModel):
    original_text: str
    translated_text: str
    source_language: str
    target_language: str
    model_used: str

# Ollama client
class OllamaClient:
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
    
    async def translate(self, text: str, source_lang: str, target_lang: str, model: str) -> str:
        prompt = f"""Please translate the following text from {source_lang} to {target_lang}. 
Only return the translation, no explanations:

Text to translate: {text}"""
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": model,
                        "prompt": prompt,
                        "stream": False
                    }
                )
                response.raise_for_status()
                result = response.json()
                return result.get("response", "Translation failed").strip()
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Translation failed: {str(e)}")

# Initialize Ollama client
ollama_client = OllamaClient()

# Root endpoint
@app.get("/")
async def read_root():
    return {
        "message": "LLM Translation Service is running!",
        "status": "online",
        "endpoints": {
            "translate": "/translate",
            "health": "/health",
            "models": "/models"
        }
    }

# Health check
@app.get("/health")
async def health_check():
    try:
        # Test Ollama connection
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get("http://localhost:11434/api/tags")
            if response.status_code == 200:
                return {"status": "healthy", "ollama": "connected", "message": "Service ready for translations"}
            else:
                return {"status": "degraded", "ollama": "disconnected", "message": "Ollama not responding"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

# Get available models
@app.get("/models")
async def get_models():
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get("http://localhost:11434/api/tags")
            if response.status_code == 200:
                models = response.json()
                return {"models": [model["name"] for model in models.get("models", [])]}
            else:
                raise HTTPException(status_code=500, detail="Failed to fetch models")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching models: {str(e)}")

# Translation endpoint
@app.post("/translate", response_model=TranslationResponse)
async def translate_text(request: TranslationRequest):
    try:
        # Perform translation
        translated_text = await ollama_client.translate(
            text=request.text,
            source_lang=request.source_language,
            target_lang=request.target_language,
            model=request.model
        )
        
        return TranslationResponse(
            original_text=request.text,
            translated_text=translated_text,
            source_language=request.source_language,
            target_language=request.target_language,
            model_used=request.model
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Translation error: {str(e)}")

# CORS middleware for remote access
@app.middleware("http")
async def add_cors_header(request, call_next):
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

if __name__ == "__main__":
    print("🚀 Starting LLM Translation Service for remote access...")
    print("📡 Service will be accessible from network at: http://0.0.0.0:8000")
    print("🔗 API Documentation: http://0.0.0.0:8000/docs")
    print("🏥 Health Check: http://0.0.0.0:8000/health")
    
    # Run on all interfaces (0.0.0.0) for network access
    uvicorn.run(
        app, 
        host="0.0.0.0",  # Allow access from any network interface
        port=8000,
        reload=False
    )
