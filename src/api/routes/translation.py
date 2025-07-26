"""
Translation API routes compatible with Baidu Translate API.
"""

from fastapi import APIRouter, Form, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Optional
import uuid

from ...models.schemas import TranslationRequest, TranslationResponse, SupportedLanguagesResponse
from ...services.translation_service import translation_service
from ...services.auth_service import auth_service
from ...services.cache_service import cache_service

# Mock logger
class MockLogger:
    def info(self, msg, **kwargs): pass
    def error(self, msg, **kwargs): pass
    def warning(self, msg, **kwargs): pass

logger = MockLogger()

router = APIRouter()


async def validate_rate_limit(app_id: str) -> bool:
    """Check rate limits for API key."""
    try:
        # Get rate limits for the app
        rate_limits = await auth_service.get_rate_limits(app_id)
        if not rate_limits:
            return True  # Allow if no limits configured
        
        # Check minute limit
        async with cache_service:
            minute_check = await cache_service.rate_limit_check(
                key=f"rate_limit:minute:{app_id}",
                limit=rate_limits["per_minute"],
                window_seconds=60
            )
            
            if not minute_check["allowed"]:
                raise HTTPException(
                    status_code=429,
                    detail={
                        "error_code": "RATE_LIMIT_EXCEEDED",
                        "error_msg": "Rate limit exceeded for this minute",
                        "remaining": minute_check["remaining"]
                    }
                )
            
            # Check hour limit
            hour_check = await cache_service.rate_limit_check(
                key=f"rate_limit:hour:{app_id}",
                limit=rate_limits["per_hour"],
                window_seconds=3600
            )
            
            if not hour_check["allowed"]:
                raise HTTPException(
                    status_code=429,
                    detail={
                        "error_code": "RATE_LIMIT_EXCEEDED",
                        "error_msg": "Rate limit exceeded for this hour",
                        "remaining": hour_check["remaining"]
                    }
                )
            
            # Check day limit
            day_check = await cache_service.rate_limit_check(
                key=f"rate_limit:day:{app_id}",
                limit=rate_limits["per_day"],
                window_seconds=86400
            )
            
            if not day_check["allowed"]:
                raise HTTPException(
                    status_code=429,
                    detail={
                        "error_code": "RATE_LIMIT_EXCEEDED",
                        "error_msg": "Rate limit exceeded for this day",
                        "remaining": day_check["remaining"]
                    }
                )
        
        return True
        
    except HTTPException:
        raise
    except Exception as e:
        logger.warning("Rate limit check failed", app_id=app_id, error=str(e))
        return True  # Allow request if rate limiting is down


@router.post("/trans/vip/translate", response_model=TranslationResponse)
async def translate_text(
    q: str = Form(..., description="Text to translate"),
    from_lang: str = Form(..., alias="from", description="Source language code"),
    to_lang: str = Form(..., alias="to", description="Target language code"),
    appid: str = Form(..., description="Application ID"),
    salt: str = Form(..., description="Random salt"),
    sign: str = Form(..., description="Request signature")
) -> TranslationResponse:
    """
    Translate text using local LLM with Baidu Translate API compatibility.
    
    This endpoint mimics the Baidu Translate API format for easy integration.
    """
    request_id = str(uuid.uuid4())
    
    try:
        logger.info(
            "Translation request received",
            request_id=request_id,
            app_id=appid,
            from_lang=from_lang,
            to_lang=to_lang,
            text_length=len(q)
        )
        
        # Validate authentication
        auth_result = await auth_service.validate_request(
            app_id=appid,
            query_text=q,
            from_lang=from_lang,
            to_lang=to_lang,
            salt=salt,
            sign=sign
        )
        
        if not auth_result["valid"]:
            logger.warning(
                "Authentication failed",
                request_id=request_id,
                app_id=appid,
                error=auth_result["error_code"]
            )
            
            return TranslationResponse(
                **{"from": from_lang, "to": to_lang},  # Use aliases
                trans_result=[],
                error_code=auth_result["error_code"],
                error_msg=auth_result["error_msg"]
            )
        
        # Check rate limits
        await validate_rate_limit(appid)
        
        # Create translation request (use alias names for Pydantic)
        translation_request = TranslationRequest(
            q=q,
            **{"from": from_lang, "to": to_lang},  # Use aliases
            appid=appid,
            salt=salt,
            sign=sign
        )
        
        # Perform translation
        result = await translation_service.translate(
            request=translation_request,
            request_id=request_id
        )
        
        logger.info(
            "Translation completed",
            request_id=request_id,
            app_id=appid,
            success=(result.error_code is None)
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Translation endpoint error",
            request_id=request_id,
            error=str(e)
        )
        
        return TranslationResponse(
            **{"from": from_lang, "to": to_lang},  # Use aliases
            trans_result=[],
            error_code="INTERNAL_ERROR",
            error_msg="Internal server error"
        )


@router.get("/languages", response_model=SupportedLanguagesResponse)
async def get_supported_languages() -> SupportedLanguagesResponse:
    """Get list of supported languages."""
    return SupportedLanguagesResponse(
        languages={
            "en": "English",
            "zh": "Chinese", 
            "auto": "Auto-detect"
        }
    )


@router.post("/demo/translate")
async def demo_translate(
    q: str = Form(..., description="Text to translate"),
    from_lang: str = Form("en", alias="from", description="Source language"),
    to_lang: str = Form("zh", alias="to", description="Target language")
):
    """
    Demo translation endpoint that generates proper signature for testing.
    
    This endpoint is useful for testing the service without needing to 
    calculate signatures manually. Includes detailed timing breakdown.
    """
    import time
    
    try:
        start_time = time.time()
        
        # Generate demo request with proper signature
        demo_request = auth_service.generate_demo_request(q, from_lang, to_lang)
        
        # Create translation request
        translation_request = TranslationRequest(
            q=demo_request["q"],
            **{"from": demo_request["from"], "to": demo_request["to"]},  # Use aliases
            appid=demo_request["appid"],
            salt=demo_request["salt"],
            sign=demo_request["sign"]
        )
        
        # Perform translation
        result = await translation_service.translate(translation_request)
        
        total_time = time.time() - start_time
        
        # Extract timing information if available
        timing_breakdown = None
        if hasattr(result, '__dict__') and 'timing_breakdown' in result.__dict__:
            timing_breakdown = result.__dict__['timing_breakdown']
        elif hasattr(result, 'timing_breakdown'):
            timing_breakdown = result.timing_breakdown
        
        # Debug: print what we have
        print(f"DEBUG - Result type: {type(result)}")
        print(f"DEBUG - Result dict: {result.__dict__ if hasattr(result, '__dict__') else 'No __dict__'}")
        print(f"DEBUG - Timing breakdown: {timing_breakdown}")
        
        response_data = {
            "request": demo_request,
            "response": result.dict(),
            "performance": {
                "total_time_ms": round(total_time * 1000, 2),
                "timing_breakdown": timing_breakdown
            }
        }
        
        return response_data
        
    except Exception as e:
        logger.error("Demo translate error", error=str(e))
        raise HTTPException(
            status_code=500,
            detail={"error": str(e)}
        )


@router.get("/demo/signature")
async def generate_demo_signature(
    q: str,
    from_lang: str = "en",
    to_lang: str = "zh"
):
    """
    Generate a demo request with proper signature for API testing.
    
    This endpoint helps developers understand how to create proper signatures.
    """
    try:
        demo_request = auth_service.generate_demo_request(q, from_lang, to_lang)
        
        return {
            "message": "Use these parameters for API testing",
            "endpoint": "/api/trans/vip/translate",
            "method": "POST",
            "content_type": "application/x-www-form-urlencoded",
            "parameters": demo_request,
            "curl_example": f"""curl -X POST "http://localhost:8888/api/trans/vip/translate" \\
     --noproxy "*" \\
     -H "Content-Type: application/x-www-form-urlencoded" \\
     -d "q={demo_request['q']}" \\
     -d "from={demo_request['from']}" \\
     -d "to={demo_request['to']}" \\
     -d "appid={demo_request['appid']}" \\
     -d "salt={demo_request['salt']}" \\
     -d "sign={demo_request['sign']}\""""
        }
        
    except Exception as e:
        logger.error("Demo signature generation error", error=str(e))
        raise HTTPException(
            status_code=500,
            detail={"error": str(e)}
        )
