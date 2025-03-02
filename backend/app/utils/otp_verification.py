#  app/utils/otp_verification.py

import json
from app.utils.redis_data_storage import RedisDataStorage
from fastapi import HTTPException
import logging
from app.utils.common_icons import event_icons  # Import event icons for easy access

# Initialize logger
logger = logging.getLogger("uvicorn.error")

async def verify_otp(redis_key: str, otp: str) -> dict:
    """
    Verify the OTP stored in Redis using the session ID.
    """
    try:
        # Step 1: Retrieve stored user data from Redis using the session ID
        user_data = RedisDataStorage.get_data_from_redis(redis_key)
        logger.info(f"{event_icons['redis.key.read']} User data retrieved from Redis for session: {redis_key}")

        if not user_data:
            logger.warning(f"{event_icons['system.error']} No data found for session: {redis_key}")
            raise HTTPException(status_code=400, detail="No data found for session.")

        # Step 2: Validate OTP
        if user_data.get("otp") != otp:
            logger.warning(f"{event_icons['notification.read']} Invalid OTP for session: {redis_key}")
            raise HTTPException(status_code=400, detail="Invalid or expired OTP.")

        # Step 3: Remove OTP from the user data
        user_data.pop("otp", None)
        logger.info(f"{event_icons['otpVerify']} OTP verified successfully for session: {redis_key}")

        return user_data

    except Exception as e:
        logger.error(f"{event_icons['system.error']} Error verifying OTP for session {redis_key}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error verifying OTP: {str(e)}")
