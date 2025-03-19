# app/middleware/session_middleware.py

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import logging
import uuid
from fastapi import Request, HTTPException
import json
from app.config import config
from app.database.redisclient import redis_client

logger = logging.getLogger(__name__)

class RedisSessionMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, paths_to_handle=None):
        super().__init__(app)
        self.redis = redis_client
        self.paths_to_handle = paths_to_handle or ["/register", "/otpVerify"]
        logger.info(f"Redis session middleware initialized.")

    async def dispatch(self, request: Request, call_next):
        try:
            if request.url.path in self.paths_to_handle:
                session_id = request.headers.get("session-id") or request.cookies.get("session_id")
                new_session = False

                if not session_id:
                    session_id = str(uuid.uuid4())
                    new_session = True
                    main_session_data = {
                        "session_id": session_id,
                        "user_session": {},
                        "otp_session": {}
                    }
                    await self.store_main_session(session_id, main_session_data)
                    logger.info(f"New session created: {session_id}")
                else:
                    main_session_data = await self.get_main_session(session_id)
                    if not main_session_data:
                        logger.warning(f"Session data not found for session_id: {session_id}")
                        raise HTTPException(status_code=400, detail="Session expired or invalid.")
                    logger.info(f"Loaded session data for session_id: {session_id}")

                request.state.session_id = session_id
                request.state.session_data = main_session_data

                response = await call_next(request)

                if new_session:
                    response.set_cookie(
                        "session_id", session_id,
                        httponly=True, secure=True, samesite="lax",
                        max_age=config.session_expiration_time['session'],
                    )

                return response

            return await call_next(request)

        except HTTPException as e:
            logger.error(f"Error in Redis session middleware: {e.detail}")
            return JSONResponse(status_code=e.status_code, content={"message": e.detail})
        except Exception as e:
            logger.error(f"Error in Redis session middleware: {e}")
            return JSONResponse(status_code=500, content={"message": "Internal server error"})

    async def store_main_session(self, session_id: str, session_data: dict):
        try:
            redis_key = f"main_session:{session_id}"
            redis_value = json.dumps(session_data)
            await self.redis.setex(redis_key, config.session_expiration_time['main_session'], redis_value)
            logger.info(f"Session stored successfully: {redis_key}")
        except Exception as e:
            logger.error(f"Failed to store session in Redis for key {redis_key}. Error: {str(e)}")

    async def get_main_session(self, session_id: str) -> dict:
        try:
            key = f"main_session:{session_id}"
            session_data = await self.redis.get(key)
            if session_data:
                return json.loads(session_data)
            return {}
        except Exception as e:
            logger.error(f"Failed to get main session from Redis: {e}")
            raise HTTPException(status_code=500, detail="Session retrieval failed")