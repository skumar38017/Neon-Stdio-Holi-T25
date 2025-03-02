# app/routes/websocket_routes.py

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.websocket_service import WebSocketHandler
import logging
from app.utils.common_icons import event_icons

# Create logger
logger = logging.getLogger("uvicorn.error")

# Create router instance
router = APIRouter()
ws_handler = WebSocketHandler()

@router.websocket("/ws")
async def websocket_general_endpoint(websocket: WebSocket):
    """
    General WebSocket endpoint for real-time communication.
    """
    logger.info(f"{event_icons['websocket_general_endpoint']} New connection established.")
    await ws_handler.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            logger.info(f"{event_icons['OTP_status_WebSocket_message_received.']} Message received: {data}")
            await ws_handler.send_message(websocket, f"Message received: {data}")
    except WebSocketDisconnect:
        logger.info(f"{event_icons['OTP_status_WebSocket_disconnected.']} WebSocket disconnected.")
        await ws_handler.disconnect(websocket)

@router.websocket("/ws/realtime")
async def websocket_realtime_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time communication.
    """
    logger.info(f"{event_icons['websocket_realtime_endpoint']} New real-time connection established.")
    await ws_handler.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            logger.info(f"{event_icons['OTP_status_WebSocket_message_received.']} Real-time message received: {data}")
            await ws_handler.send_message(websocket, f"Message received: {data}")
    except WebSocketDisconnect:
        logger.info(f"{event_icons['OTP_status_WebSocket_disconnected.']} Real-time WebSocket disconnected.")
        await ws_handler.disconnect(websocket)

@router.websocket("/ws/otp_status")
async def websocket_otp_status_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint to send OTP status updates.
    This endpoint listens for OTP task-related requests and sends updates.
    """
    logger.info(f"{event_icons['websocket_otp_status_endpoint']} New OTP status connection established.")
    await ws_handler.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            logger.info(f"{event_icons['OTP_status_WebSocket_message_received.']} OTP status message received: {data}")
            if data.startswith("subscribe:"):
                phone_no = data.split(":")[1]
                logger.info(f"{event_icons['Client_subscribed']} Client subscribed to OTP status updates for phone: {phone_no}")
                await ws_handler.subscribe(phone_no, websocket)
                await ws_handler.send_message(websocket, f"Subscribed to OTP updates for {phone_no}.")
            elif data == "ping":
                logger.info(f"{event_icons['OTP_status_WebSocket_ping_received.']} Ping received, sending pong.")
                await websocket.send_text("pong")
            else:
                logger.warning(f"{event_icons['OTP_status_WebSocket_message_received.']} Unhandled message format.")
                await ws_handler.send_message(websocket, "Unhandled message format.")
    except WebSocketDisconnect:
        logger.info(f"{event_icons['OTP_status_WebSocket_disconnected.']} OTP status WebSocket disconnected.")
        await ws_handler.disconnect(websocket)

@router.websocket("/ws/session")
async def websocket_session_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for session notifications and health checks.
    """
    logger.info(f"{event_icons['websocket_session_endpoint']} New session WebSocket connection established.")
    await ws_handler.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            logger.info(f"{event_icons['OTP_status_WebSocket_message_received.']} Session message received: {data}")
            if data == "ping":
                logger.info(f"{event_icons['Ping_received_sending_pong.']} Ping received, sending pong.")
                await websocket.send_text("pong")
            else:
                logger.warning(f"{event_icons['OTP_status_WebSocket_message_received.']} Unhandled session message.")
                await ws_handler.send_message(websocket, f"Unhandled message: {data}")
    except WebSocketDisconnect:
        logger.info(f"{event_icons['OTP_status_WebSocket_disconnected.']} Session WebSocket disconnected.")
        await ws_handler.disconnect(websocket)
