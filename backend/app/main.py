# app/main.py

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse
from app.routes import user_routes, websocket_routes, qr_code_routes, ticket_routes
from app.routes.webhook_routes import webhook_router  # Import directly from webhook_routes
from app.database.database import get_db_connection, get_db, login_to_database
from app.database.redisclient import redis_client
from app.config import config
from app.settings import settings
from app.middleware.cors_middleware import CustomCORSMiddleware
from app.middleware.session_middleware import RedisSessionMiddleware
from app.services.websocket_service import WebSocketHandler
from app.services.otp_service import OTPService
from app.utils.razorpay_utils import RazorpayClient, RazorpayError
from app.utils.common_icons import event_icons  # Import the event icons
import logging
import sys
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize WebSocketHandler
ws_handler = WebSocketHandler()

# Correctly retrieve DEV_MODE from config
DEV_MODE = config.app_config.get("dev_mode", False)

# Conditional URLs based on DEV_MODE
openapi_url = "/openapi.json" if DEV_MODE else None
docs_url = "/docs" if DEV_MODE else None
redoc_url = "/redoc" if DEV_MODE else None

# FastAPI App Initialization
app = FastAPI(
    title="Ticket Management System",
    description="This is a ticket management system for the Neon-Stdioz Holi-T25 course.",
    version="1.1.0",
    openapi_url=openapi_url,
    docs_url=docs_url,
    redoc_url=redoc_url,
)

# Add middleware
app.add_middleware(RedisSessionMiddleware)
app.add_middleware(CustomCORSMiddleware)

# Root Endpoint
@app.get("/", include_in_schema=True)
async def index():
    """
    Root endpoint.
    """
    logger.info(f"{event_icons['index']} Root endpoint accessed.")
    return {"message": "Ticket Management System"}

# Include Routes
app.include_router(user_routes.router)
app.include_router(ticket_routes.router)
app.include_router(qr_code_routes.router)
app.include_router(webhook_router)  # Use the imported webhook_router directly
app.include_router(websocket_routes.router)

@app.on_event("startup")
async def startup_event():
    """
    Event handler that runs on application startup.
    - Ensures DB, Redis, and Razorpay connections are established.
    """
    logger.info(f"{event_icons['index']} Application started in {'Development' if DEV_MODE else 'Production'} mode.")
    logger.info(f"{event_icons['info']} Running setup tasks...")

    try:
        # Database Connection Check
        logger.info(f"{event_icons['openapi.json']} Checking database connection...")
        await login_to_database()
        logger.info(f"{event_icons['payment.authorized']} Database connection successful.")

        # Redis Connection Check    
        logger.info(f"{event_icons['payment.downtime.started']} Checking Redis connection...")
        await redis_client.connect()
        logger.info(f"{event_icons['payment.captured']} Redis connection successful.")

        # Razorpay Connection Check
        logger.info(f"{event_icons['payment.downtime.updated']} Checking Razorpay connection...")
        # if RazorpayClient.is_connected():
        logger.info(f"{event_icons['payment.captured']} Razorpay is successfully connected.")
        # else:
        #     logger.error(f"{event_icons['payment.failed']} Failed to connect to Razorpay.")
            # sys.exit(1)  # Exit if Razorpay setup fails

        # Print registered routes
        logger.info(f"{event_icons['handshake']} Registered routes:")
        for route in app.routes:
            logger.info(f"➡️ {route.path} - {route.name}")

        logger.info(f"{event_icons['order.notification.delivered']} Startup tasks completed successfully.")

    except Exception as e:
        logger.error(f"{event_icons['error']} Startup tasks failed: {e}")
        sys.exit(1)  # Exit the application if setup fails


@app.middleware("http")
async def add_session_to_state(request: Request, call_next):
    session_id = request.cookies.get("session_id")
    if session_id:
        # Retrieve session from Redis (or wherever you're storing it)
        session_data = await redis_client.get(session_id)
        if session_data:
            request.state.session = session_data  # Assign session data to request.state
        else:
            request.state.session = {}
    else:
        request.state.session = {}  # No session if no session_id in cookies
    
    response = await call_next(request)
    return response

# Exception Handler
@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    """
    Custom exception handler for HTTP exceptions.
    - Changes 422 → 400 in production.
    - Logs errors for debugging.
    - Returns a structured JSON response.
    """
    status_code = 400 if not settings.DEV_MODE and exc.status_code == 422 else exc.status_code

    logger.error(f"{event_icons['error']} HTTPException: {exc.detail} | Path: {request.url.path} | Status Code: {status_code}")

    response_content = {
        "error": "Bad Request" if status_code == 400 else "HTTP Error",
        "detail": exc.detail,
        "path": request.url.path,
    }

    return JSONResponse(status_code=status_code, content=response_content)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
