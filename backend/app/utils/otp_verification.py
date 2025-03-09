# app/utils/otp_verification.py

import time
from app.utils.redis_data_storage import RedisDataStorage
from fastapi import HTTPException
import logging

logger = logging.getLogger("uvicorn.error")

async def verify_otp(session_id: str, otp: str) -> dict:
    """
    Verifies OTP and retrieves user data from `main_session`.
    """
    try:
        # Retrieve main session data
        main_session_data = await RedisDataStorage.get_data_from_redis("main_session", session_id)
        if not main_session_data:
            logger.warning(f"⚠️ Main session data not found for session: {session_id}")
            raise HTTPException(status_code=400, detail="Session expired or invalid.")

        # Extract OTP session data
        otp_session_data = main_session_data.get("otp_session")
        if not otp_session_data:
            logger.warning(f"⚠️ OTP session data not found for session: {session_id}")
            raise HTTPException(status_code=400, detail="OTP expired or not found.")

        # Check if OTP is expired
        current_time = int(time.time())
        if current_time > otp_session_data.get("otp_expiration_time", current_time):
            logger.warning(f"⚠️ OTP expired for session: {session_id}")
            raise HTTPException(status_code=400, detail="OTP expired.")

        # Verify OTP
        if otp_session_data.get("otp") != otp:
            logger.warning(f"❌ Invalid OTP for session: {session_id}")
            raise HTTPException(status_code=400, detail="Invalid OTP.")

        # Extract user session data
        user_session_data = main_session_data.get("user_session")
        if not user_session_data:
            logger.warning(f"⚠️ User session data not found for session: {session_id}")
            raise HTTPException(status_code=400, detail="Session expired or invalid.")

        # Cleanup temporary sessions
        main_session_data.pop("otp_session", None)
        main_session_data.pop("user_session", None)

        # Update main session data in Redis
        await RedisDataStorage.store_data_in_redis("main_session", session_id, main_session_data)

        logger.info(f"✅ OTP verified successfully. Data retrieved from main_session: {session_id}")
        return user_session_data

    except HTTPException as e:
        logger.error(f"❌ Error verifying OTP: {e.detail}")
        raise
    except Exception as e:
        logger.error(f"❌ Error verifying OTP: {str(e)}")
        raise HTTPException(status_code=500, detail="Error verifying OTP")