#!/usr/bin/env python3
"""
Main entry point for the LLM Translation Service.
"""

import uvicorn
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.core.config import get_settings

def main():
    """Run the translation service."""
    settings = get_settings()
    
    uvicorn.run(
        "src.main:app",
        host=settings.api.host,
        port=settings.api.port,
        workers=settings.api.workers,
        reload=settings.debug,
        log_level=settings.logging.log_level.lower()
    )

if __name__ == "__main__":
    main()
