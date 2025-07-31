"""
FastAPI application setup and configuration.
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
import time
import os
from pathlib import Path

from .core.config import get_settings
from .core.network import NetworkManager
from .api.routes import translation, health, admin, discovery, optimized, chatbot, user_management, file_upload, tts, background_music, phase4_status
from .api.routes import voice_chat as voice_chat_routes
from .api.routes import phone_call as phone_call_routes

# Mock logger
class MockLogger:
    def info(self, msg, **kwargs): pass
    def error(self, msg, **kwargs): pass
    def warning(self, msg, **kwargs): pass

logger = MockLogger()


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    
    settings = get_settings()
    network_manager = NetworkManager(settings)
    
    # Create FastAPI app
    app = FastAPI(
        title=settings.api.title,
        description=settings.api.description,
        version=settings.api.version,
        debug=settings.debug,
        docs_url=None,  # Disable default docs, we'll handle it ourselves
        redoc_url=None,  # Disable default redoc, we'll handle it ourselves
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.api.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )
    
    # Add trusted host middleware (disabled for ngrok compatibility)
    # When using ngrok or similar tunneling services, we need to allow external hosts
    # For production, this should be properly configured with specific allowed hosts
    enable_host_checking = os.getenv("ENABLE_HOST_CHECKING", "false").lower() == "true"
    
    if not settings.debug and enable_host_checking:
        allowed_hosts = ["localhost", "127.0.0.1", settings.api.host]
        
        # Add additional trusted hosts for remote deployment
        if settings.deployment.mode == "remote":
            if settings.deployment.external_host:
                allowed_hosts.append(settings.deployment.external_host)
            # Add local network IP
            local_ip = network_manager.get_local_ip(settings.deployment.network_interface)
            if local_ip and local_ip not in allowed_hosts:
                allowed_hosts.append(local_ip)
        
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=allowed_hosts
        )
    
    # Add request timing middleware
    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        return response
    
    # Add global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(
            "Unhandled exception",
            path=request.url.path,
            method=request.method,
            error=str(exc)
        )
        
        return JSONResponse(
            status_code=500,
            content={
                "error_code": "INTERNAL_ERROR",
                "error_msg": "Internal server error occurred"
            }
        )
    
    # Include routers
    app.include_router(translation.router, prefix="/api")
    app.include_router(optimized.router, prefix="/api")  # Add optimized routes
    app.include_router(health.router, prefix="/api")
    app.include_router(admin.router, prefix="/api/admin")
    app.include_router(discovery.router)  # Discovery routes already have /api/discovery prefix
    app.include_router(chatbot.router)  # Add chatbot routes with /api/chat prefix
    app.include_router(user_management.router)  # Add user management routes
    app.include_router(file_upload.router)  # Add file upload and processing routes
    app.include_router(tts.router, prefix="/api")  # Add TTS routes
    app.include_router(voice_chat_routes.router)  # Add voice chat routes
    app.include_router(phone_call_routes.router)  # Add phone call routes
    app.include_router(background_music.router, prefix="/api")  # Add background music routes
    app.include_router(phase4_status.router)  # Add Phase 4 status monitoring routes
    
    # Mount static files for web interface BEFORE other routes
    web_dir = Path(__file__).parent.parent / "web"
    if web_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(web_dir / "assets")), name="assets")
        app.mount("/web", StaticFiles(directory=str(web_dir), html=True), name="web")
    
    # Chat interface route
    @app.get("/chat", response_class=HTMLResponse)
    async def chat_interface():
        web_dir = Path(__file__).parent.parent / "web"
        chat_html = web_dir / "chat.html"
        if chat_html.exists():
            return HTMLResponse(content=chat_html.read_text(encoding='utf-8'))
        else:
            return HTMLResponse(content="""
            <html><body>
                <h1>Chat Interface Not Found</h1>
                <p>The chat.html file is missing. Please ensure the web interface is properly installed.</p>
                <p><a href="/api/chat/health">Check API Health</a></p>
            </body></html>
            """)
    
    # Authentication interface route
    @app.get("/auth.html", response_class=HTMLResponse)
    async def auth_interface():
        web_dir = Path(__file__).parent.parent / "web"
        auth_html = web_dir / "auth.html"
        if auth_html.exists():
            return HTMLResponse(content=auth_html.read_text(encoding='utf-8'))
        else:
            return HTMLResponse(content="""
            <html><body>
                <h1>Authentication Interface Not Found</h1>
                <p>The auth.html file is missing. Please ensure the web interface is properly installed.</p>
                <p><a href="/chat">Go to Chat</a></p>
            </body></html>
            """, status_code=404)

    # Translation service interface route
    @app.get("/translate", response_class=HTMLResponse)
    async def translate_interface():
        web_dir = Path(__file__).parent.parent / "web"
        translate_html = web_dir / "translate.html"
        if translate_html.exists():
            return HTMLResponse(content=translate_html.read_text(encoding='utf-8'))
        else:
            return HTMLResponse(content="""
            <html><body>
                <h1>Translation Interface Not Found</h1>
                <p>The translate.html file is missing. Please ensure the web interface is properly installed.</p>
                <p><a href="/">Go to Home</a> | <a href="/api/docs">API Documentation</a></p>
            </body></html>
            """, status_code=404)

    # Translation UI interface route
    @app.get("/translate-ui", response_class=HTMLResponse)
    async def translate_ui_interface():
        web_dir = Path(__file__).parent.parent / "web"
        translate_ui_html = web_dir / "translate-ui.html"
        if translate_ui_html.exists():
            return HTMLResponse(content=translate_ui_html.read_text(encoding='utf-8'))
        else:
            return HTMLResponse(content="""
            <html><body>
                <h1>Translation UI Not Found</h1>
                <p>The translate-ui.html file is missing. Please ensure the web interface is properly installed.</p>
                <p><a href="/">Go to Home</a> | <a href="/api/docs">API Documentation</a></p>
            </body></html>
            """, status_code=404)
    
    # Authentication interface route (without .html extension)
    @app.get("/auth", response_class=HTMLResponse)
    async def auth_interface_clean():
        web_dir = Path(__file__).parent.parent / "web"
        auth_html = web_dir / "auth.html"
        if auth_html.exists():
            return HTMLResponse(content=auth_html.read_text(encoding='utf-8'))
        else:
            return HTMLResponse(content="""
            <html><body>
                <h1>Authentication Interface Not Found</h1>
                <p>The auth.html file is missing. Please ensure the web interface is properly installed.</p>
                <p><a href="/chat">Go to Chat</a></p>
            </body></html>
            """, status_code=404)

    # Live debug tool route  
    @app.get("/live-debug.html", response_class=HTMLResponse)
    async def live_debug_interface():
        web_dir = Path(__file__).parent.parent / "web"
        live_debug_html = web_dir / "live-debug.html"
        if live_debug_html.exists():
            return HTMLResponse(content=live_debug_html.read_text(encoding='utf-8'))
        else:
            return HTMLResponse(content="""
            <html><body>
                <h1>Live Debug Tool Not Found</h1>
                <p>The live-debug.html file is missing. Please ensure the web interface is properly installed.</p>
                <p><a href="/web/live-debug.html">Try /web/live-debug.html</a> | <a href="/chat">Go to Chat</a></p>
            </body></html>
            """, status_code=404)
    
    # Serve voice chat interface
    @app.get("/voice-chat", response_class=HTMLResponse)
    async def voice_chat():
        web_dir = Path(__file__).parent.parent / "web"
        voice_chat_html = web_dir / "voice-chat.html"
        
        if voice_chat_html.exists():
            return HTMLResponse(content=voice_chat_html.read_text(encoding='utf-8'))
        else:
            return HTMLResponse(content="""
            <!DOCTYPE html><html><head><title>Voice Chat Not Found</title></head>
            <body style="font-family: Arial, sans-serif; text-align: center; margin: 50px;">
                <h1>Voice Chat Interface Not Found</h1>
                <p>The voice-chat.html file is missing. Please ensure the web interface is properly installed.</p>
                <p><a href="/web/voice-chat.html">Try /web/voice-chat.html</a> | <a href="/">Go to Main Page</a></p>
            </body></html>
            """, status_code=404)
    
    # Serve phone call interface
    @app.get("/phone-call", response_class=HTMLResponse)
    async def phone_call():
        web_dir = Path(__file__).parent.parent / "web"
        phone_call_html = web_dir / "phone-call.html"
        
        if phone_call_html.exists():
            return HTMLResponse(content=phone_call_html.read_text(encoding='utf-8'))
        else:
            return HTMLResponse(content="""
            <!DOCTYPE html><html><head><title>Phone Call Not Found</title></head>
            <body style="font-family: Arial, sans-serif; text-align: center; margin: 50px;">
                <h1>Phone Call Interface Not Found</h1>
                <p>The phone-call.html file is missing. Please ensure the web interface is properly installed.</p>
                <p><a href="/web/phone-call.html">Try /web/phone-call.html</a> | <a href="/">Go to Main Page</a></p>
            </body></html>
            """, status_code=404)
    
    # Serve entrance page at root
    @app.get("/", response_class=HTMLResponse)
    async def root():
        web_dir = Path(__file__).parent.parent / "web"
        index_html = web_dir / "index.html"
        
        # Serve the new entrance page
        if index_html.exists():
            return HTMLResponse(content=index_html.read_text(encoding='utf-8'))
        else:
            # Fallback to service info if index.html doesn't exist
            service_info = network_manager.get_service_info()
            return {
                "name": settings.api.title,
                "version": settings.api.version,
                "description": settings.api.description,
                "deployment_mode": settings.deployment.mode,
                "connection_url": network_manager.get_connection_url(),
                "docs_url": "/docs" if settings.debug else None,
                "web_interface": "/web/",
                "service_discovery": "/api/discovery/info",
                "endpoints": {
                    "health": "/api/health",
                    "translate": "/api/trans/vip/translate",
                    "demo_translate": "/api/demo/translate",
                    "optimized_translate": "/api/optimized/translate",
                    "performance_stats": "/api/optimized/stats",
                    "benchmark": "/api/optimized/benchmark",
                    "chat_message": "/api/chat/message",
                    "chat_conversations": "/api/chat/conversations",
                    "chat_health": "/api/chat/health",
                    "tts_synthesize": "/api/tts/synthesize",
                    "tts_translate_speak": "/api/tts/translate-and-speak",
                    "tts_languages": "/api/tts/languages",
                    "tts_health": "/api/tts/health"
                }
            }

    # API docs redirect route
    @app.get("/api/docs")
    async def api_docs_redirect():
        # Always redirect to docs, regardless of debug mode
        return RedirectResponse(url="/docs", status_code=302)
    
    # Enable docs endpoint regardless of debug mode for API access
    @app.get("/docs", response_class=HTMLResponse)
    async def custom_docs():
        from fastapi.openapi.docs import get_swagger_ui_html
        return get_swagger_ui_html(
            openapi_url="/openapi.json",
            title=f"{settings.api.title} - API Documentation",
            swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui-bundle.js",
            swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui.css",
        )

    # Enable redoc endpoint regardless of debug mode for API access
    @app.get("/redoc", response_class=HTMLResponse)
    async def custom_redoc():
        from fastapi.openapi.docs import get_redoc_html
        return get_redoc_html(
            openapi_url="/openapi.json",
            title=f"{settings.api.title} - API Documentation (ReDoc)",
            redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@2.1.3/bundles/redoc.standalone.js",
        )

    # Service info endpoint for programmatic access
    @app.get("/api/info")
    async def service_info():
        service_info = network_manager.get_service_info()
        return {
            "name": settings.api.title,
            "version": settings.api.version,
            "description": settings.api.description,
            "deployment_mode": settings.deployment.mode,
            "connection_url": network_manager.get_connection_url(),
            "docs_url": "/docs" if settings.debug else None,
            "web_interface": "/",
            "service_discovery": "/api/discovery/info",
            "endpoints": {
                "health": "/api/health",
                "translate": "/api/trans/vip/translate",
                "demo_translate": "/api/demo/translate",
                "optimized_translate": "/api/optimized/translate",
                "performance_stats": "/api/optimized/stats",
                "benchmark": "/api/optimized/benchmark",
                "chat_message": "/api/chat/message",
                "chat_conversations": "/api/chat/conversations",
                "chat_health": "/api/chat/health",
                "tts_synthesize": "/api/tts/synthesize",
                "tts_translate_speak": "/api/tts/translate-and-speak",
                "tts_languages": "/api/tts/languages",
                "tts_health": "/api/tts/health"
            }
        }
    
    return app


# Create the app instance
app = create_app()
