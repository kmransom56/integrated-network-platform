"""
Main FastAPI Application
Unified API combining network management and 3D visualization
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import logging
from pathlib import Path

from .endpoints.devices import router as devices_router
from .endpoints.visualization import router as visualization_router
from .endpoints.topology import router as topology_router
from .endpoints.compat import router as compat_router
from .endpoints.meraki_vis import router as meraki_vis_router
from shared.config.config_manager import ConfigManager

logger = logging.getLogger(__name__)


def create_application(config_file: str = None) -> FastAPI:
    """
    Create the integrated FastAPI application
    Combines APIs from both network_map_3d and enhanced-network-api-corporate
    """

    # Load configuration
    config_manager = ConfigManager(config_file)

    # Create FastAPI app
    app = FastAPI(
        title="Integrated Network Platform API",
        description="Unified API for network device management and 3D visualization",
        version="1.0.0",
        debug=config_manager.config.debug_mode
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount static files for 3D visualization assets
    static_dir = config_manager.config.exports_dir / "static"
    static_dir.mkdir(parents=True, exist_ok=True)
    
    # Mount UI static files (from network-d3js)
    ui_dir = static_dir / "ui"
    ui_dir.mkdir(parents=True, exist_ok=True)

    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    app.mount("/ui", StaticFiles(directory=str(ui_dir), html=True), name="ui")
    app.mount("/models", StaticFiles(directory=str(config_manager.config.models_dir)), name="models")
    app.mount("/icons", StaticFiles(directory=str(config_manager.config.icons_dir)), name="icons")

    # Include API routers
    app.include_router(
        devices_router,
        prefix="/api/v1/devices",
        tags=["devices"]
    )

    app.include_router(
        visualization_router,
        prefix="/api/v1/visualization",
        tags=["visualization"]
    )

    app.include_router(
        topology_router,
        prefix="/api/v1/topology",
        tags=["topology"]
    )

    app.include_router(
        compat_router,
        prefix="/api",
        tags=["compatibility"]
    )

    app.include_router(
        meraki_vis_router,
        prefix="/api/meraki",
        tags=["meraki"]
    )

    # Store config in app state
    app.state.config = config_manager

    @app.get("/", response_class=HTMLResponse)
    async def root():
        """Root endpoint - Landing Page"""
        landing_path = config_manager.config.exports_dir / "static" / "landing.html"
        if landing_path.exists():
            with open(landing_path, "r") as f:
                return f.read()
        return """
        <html><body>
        <h1> Integrated Network Platform </h1>
        <p> Landing page not found. Please verify setup. </p>
        <a href="/docs"> API Docs </a> <br>
        <a href="/ui/"> D3 Map </a>
        </body></html>
        """

    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return {
            "status": "healthy",
            "services": {
                "config": "loaded",
                "database": "ready",  # Would check actual DB connection
                "network_clients": "initialized"
            }
        }

    @app.get("/config/status")
    async def config_status(request: Request):
        """Configuration status endpoint"""
        config = request.app.state.config

        # Get safe credentials for UI pre-fill
        creds = config.get_network_credentials()
        safe_creds = {
            "fortigate": {
                "host": creds['fortigate']['host'],
                "username": creds['fortigate']['username']
            },
            "meraki": {
                "configured": bool(creds['meraki']['api_key'])
            }
        }

        return {
            "fortigate_configured": config.is_configured('fortigate'),
            "fortimanager_configured": config.is_configured('fortimanager'),
            "meraki_configured": config.is_configured('meraki'),
            "credentials": safe_creds,
            "paths": {
                "data_dir": str(config.config.data_dir),
                "exports_dir": str(config.config.exports_dir),
                "models_dir": str(config.config.models_dir)
            },
            "features": {
                "3d_enabled": config.config.enable_3d,
                "renderer": config.config.renderer,
                "cache_enabled": config.config.cache_enabled
            }
        }

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Global exception handler"""
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "message": str(exc),
                "path": str(request.url)
            }
        )

    logger.info("Integrated Network Platform API initialized")
    return app


if __name__ == "__main__":
    import uvicorn

    # Create and run the application
    app = create_application()

    # Get port from environment or default to 8000
    port = int(os.getenv("PORT", 11100))

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )