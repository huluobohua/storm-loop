"""
Main entry point for STORM-Loop application
"""
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from storm_loop.config import get_config
from storm_loop.utils.logging import storm_logger


def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    config = get_config()
    
    app = FastAPI(
        title="STORM-Loop",
        description="Enhanced Academic Knowledge Curation System",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    @app.on_event("startup")
    async def startup_event():
        """Application startup tasks"""
        storm_logger.info("Starting STORM-Loop application")
        storm_logger.info(f"Operation mode: {config.mode}")
        storm_logger.info(f"Redis host: {config.redis_host}:{config.redis_port}")
    
    @app.on_event("shutdown")
    async def shutdown_event():
        """Application shutdown tasks"""
        storm_logger.info("Shutting down STORM-Loop application")
    
    @app.get("/")
    async def root():
        """Root endpoint"""
        return {
            "message": "STORM-Loop API",
            "version": "0.1.0",
            "mode": config.mode,
            "status": "running"
        }
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return {"status": "healthy", "mode": config.mode}
    
    @app.get("/config")
    async def get_app_config():
        """Get application configuration (non-sensitive data only)"""
        return {
            "mode": config.mode,
            "redis_host": config.redis_host,
            "redis_port": config.redis_port,
            "enable_openalex": config.enable_openalex,
            "enable_crossref": config.enable_crossref,
            "max_concurrent_requests": config.max_concurrent_requests,
            "enable_citation_verification": config.enable_citation_verification,
            "enable_grammar_checking": config.enable_grammar_checking,
        }
    
    return app


app = create_app()


def main():
    """Main function to run the application"""
    config = get_config()
    storm_logger.info("Starting STORM-Loop server")
    
    uvicorn.run(
        "storm_loop.main:app",
        host="0.0.0.0",
        port=8000,
        log_level=config.log_level.lower(),
        reload=True if config.log_level == "DEBUG" else False,
    )


if __name__ == "__main__":
    main()