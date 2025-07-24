#!/usr/bin/env python3
"""
Simple test to check if the basic setup works
"""

from fastapi import FastAPI
import uvicorn

# Create a simple FastAPI app
app = FastAPI(title="LLM Translation Test")

@app.get("/")
async def read_root():
    return {"message": "Hello! Translation service is running on Windows!"}

@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "Service is healthy"}

if __name__ == "__main__":
    print("Starting simple translation service test...")
    uvicorn.run(app, host="127.0.0.1", port=8000)
