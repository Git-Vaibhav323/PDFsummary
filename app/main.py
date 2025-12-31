"""
Main entry point for the RAG chatbot application.
"""
import logging
import socket
import sys
import uvicorn
from app.config.settings import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def is_port_available(host: str, port: int) -> bool:
    """Check if a port is available."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex((host, port))
            return result != 0  # Port is available if connection fails
    except Exception:
        return False


def find_available_port(host: str, start_port: int, max_attempts: int = 10) -> int:
    """Find an available port starting from start_port."""
    for i in range(max_attempts):
        port = start_port + i
        if is_port_available(host, port):
            return port
    return None


def main():
    """Run the FastAPI application."""
    # Render provides PORT environment variable, use it if available
    import os
    port = int(os.environ.get("PORT", settings.api_port))
    host = settings.api_host
    
    # In production (Render), use 0.0.0.0 to bind to all interfaces
    if os.environ.get("RENDER") or os.environ.get("PORT"):
        host = "0.0.0.0"
        logger.info(f"Running in production mode (Render detected)")
    
    # Check if port is available (skip in production)
    if not os.environ.get("RENDER") and not os.environ.get("PORT"):
        if not is_port_available(host, port):
            logger.warning(f"Port {port} is already in use. Searching for available port...")
            available_port = find_available_port(host, port)
            if available_port:
                logger.info(f"Using alternative port: {available_port}")
                port = available_port
            else:
                logger.error(f"Could not find an available port starting from {settings.api_port}")
                logger.error("Please close the application using port 8000 or specify a different port in .env")
                sys.exit(1)
    
    logger.info("Starting PDF Chatbot API...")
    logger.info(f"API will be available at http://{host}:{port}")
    logger.info(f"API docs will be available at http://{host}:{port}/docs")
    
    # Import the app to ensure all imports are loaded before uvicorn starts
    from app.api.routes import app as fastapi_app
    logger.info("✅ FastAPI app imported successfully")
    
    try:
        # Use the direct app object instead of string import for faster startup
        uvicorn.run(
            fastapi_app,
            host=host,
            port=port,
            reload=False,
            log_level="info",
            timeout_keep_alive=600,  # 10 minutes keep-alive timeout
            timeout_graceful_shutdown=30,  # 30 seconds graceful shutdown
            workers=1  # Single worker for free tier
        )
    except OSError as e:
        if "10048" in str(e) or "address already in use" in str(e).lower():
            logger.error(f"Port {port} is already in use. Please:")
            logger.error(f"  1. Close the application using port {port}")
            logger.error(f"  2. Or change API_PORT in your .env file")
            logger.error(f"  3. Or run: netstat -ano | findstr :{port}  (to find the process)")
        else:
            logger.error(f"Error starting server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

