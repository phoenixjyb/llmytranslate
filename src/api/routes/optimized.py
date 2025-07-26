"""
Optimized Translation API Routes
"""

from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import JSONResponse
import time
import logging

# Import the optimized service
from ...services.optimized_translation_service import optimized_translation_service, TranslationRequest

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/optimized/translate")
async def optimized_translate(
    q: str = Form(..., description="Text to translate"),
    from_lang: str = Form("en", alias="from", description="Source language"),
    to_lang: str = Form("zh", alias="to", description="Target language"),
    model: str = Form(None, description="Model to use (optional)"),
    use_cache: bool = Form(True, description="Use caching")
):
    """
    Optimized translation endpoint with:
    - Connection pooling and keep-alive
    - Enhanced caching with compression
    - Detailed timing breakdown
    - Performance metrics
    """
    
    try:
        # Initialize if needed
        await optimized_translation_service.initialize()
        
        # Create translation request
        request = TranslationRequest(
            text=q,
            from_lang=from_lang,
            to_lang=to_lang,
            model=model,
            use_cache=use_cache
        )
        
        # Perform translation
        result = await optimized_translation_service.translate(request)
        
        if result.success:
            # Format response with detailed timing
            response_data = {
                "success": True,
                "translation": result.translation,
                "cached": result.cached,
                "model_used": result.model_used,
                "timing_breakdown": result.timing_breakdown,
                "performance_metrics": result.performance_metrics,
                "request": {
                    "text": q,
                    "from": from_lang,
                    "to": to_lang,
                    "model": model or "default",
                    "use_cache": use_cache
                }
            }
            
            return JSONResponse(content=response_data)
        else:
            raise HTTPException(
                status_code=500,
                detail={
                    "success": False,
                    "error": result.error,
                    "timing_breakdown": result.timing_breakdown
                }
            )
            
    except Exception as e:
        logger.error(f"Optimized translate error: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": str(e)}
        )

@router.get("/optimized/stats")
async def get_optimization_stats():
    """Get comprehensive performance statistics."""
    try:
        stats = optimized_translation_service.get_performance_stats()
        return JSONResponse(content=stats)
        
    except Exception as e:
        logger.error(f"Stats error: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": str(e)}
        )

@router.post("/optimized/benchmark")
async def run_benchmark():
    """Run performance optimization and benchmarking."""
    try:
        optimization_result = await optimized_translation_service.optimize_performance()
        return JSONResponse(content=optimization_result)
        
    except Exception as e:
        logger.error(f"Benchmark error: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": str(e)}
        )

@router.get("/optimized/models")
async def get_available_models():
    """Get list of available models."""
    try:
        models = await optimized_translation_service.get_available_models()
        return JSONResponse(content={"models": models})
        
    except Exception as e:
        logger.error(f"Models error: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": str(e)}
        )
