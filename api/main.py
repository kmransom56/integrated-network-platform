"""
Main FastAPI Application
Unified API combining network management and 3D visualization
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import logging
from pathlib import Path

from .endpoints.devices import router as devices_router
from .endpoints.visualization import router as visualization_router
from .endpoints.topology import router as topology_router
from ..shared.config.config_manager import ConfigManager

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

    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
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

    # Store config in app state
    app.state.config = config_manager

    @app.get("/")
    async def root():
        """Root endpoint with API information"""
        return {
            "name": "Integrated Network Platform API",
            "version": "1.0.0",
            "description": "Unified network device management and 3D visualization",
            "endpoints": {
                "devices": "/api/v1/devices",
                "visualization": "/api/v1/visualization",
                "topology": "/api/v1/topology",
                "docs": "/docs",
                "static": "/static"
            }
        }

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

        return {
            "fortigate_configured": config.is_configured('fortigate'),
            "fortimanager_configured": config.is_configured('fortimanager'),
            "meraki_configured": config.is_configured('meraki'),
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
    port = int(os.getenv("PORT", 8000))

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )