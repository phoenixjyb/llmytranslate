"""
FastAPI application setup and configuration.
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import time
import os
from pathlib import Path

from .core.config import get_settings
from .core.network import NetworkManager
from .api.routes import translation, health, admin, discovery, optimized, chatbot, user_management

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
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
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
    
    # Serve optimized interface at root
    @app.get("/", response_class=HTMLResponse)
    async def root():
        web_dir = Path(__file__).parent.parent / "web"
        chat_html = web_dir / "chat.html"
        optimized_html = web_dir / "optimized.html"
        
        # Prefer chat interface over optimized interface
        if chat_html.exists():
            return HTMLResponse(content=chat_html.read_text(encoding='utf-8'))
        elif optimized_html.exists():
            return HTMLResponse(content=optimized_html.read_text(encoding='utf-8'))
        else:
            # Fallback to service info if optimized.html doesn't exist
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
                    "chat_health": "/api/chat/health"
                }
            }
    
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
                "chat_health": "/api/chat/health"
            }
        }
    
    return app


# Create the app instance
app = create_app()
