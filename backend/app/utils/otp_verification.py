#  app/utils/otp_verification.py

import json
from app.utils.redis_data_storage import RedisDataStorage
from fastapi import HTTPException

async def verify_otp(redis_key: str, otp: str) -> dict:
    """
    Verify the OTP stored in Redis using the session ID.
    """
    # Retrieve stored user data from Redis using the session ID
    user_data = RedisDataStorage.get_data_from_redis(redis_key)
    print(f"User data from Redis: {user_data}")

    if not user_data:
        raise HTTPException(status_code=400, detail="No data found for session.")

    # Validate OTP
    if user_data.get("otp") != otp:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP.")

    # Remove OTP before saving user data
    user_data.pop("otp", None)

    return user_data
