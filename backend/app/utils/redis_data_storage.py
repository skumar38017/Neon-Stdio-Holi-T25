# app/utils/redis_data_storage.py

from typing import Optional
import json
import logging
from app.database.redisclient import redis_client
from app.config import config

logger = logging.getLogger(__name__)

class RedisDataStorage:
    session_expiration_time = {
        "main_session": config.session_expiration_time['main_session'],
        "user_session": config.session_expiration_time['user_session'],
        "otp_session": config.session_expiration_time['otp_session_expiration_time'],
    }

    @staticmethod
    async def store_data_in_redis(session_type: str, session_id: str, data: dict, expiration: int = None) -> None:
        """
        Stores data in Redis under the specified session type (main_session, user_session, otp_session).
        """
        try:
            if not isinstance(data, dict):
                raise ValueError(f"Data must be a dictionary. Received: {type(data)}")

            expiration = expiration or RedisDataStorage.session_expiration_time.get(session_type, 600)

            if session_type in ["user_session", "otp_session"]:
                # Update main_session with nested session data
                main_session_key = f"main_session:{session_id}"
                main_session_data = await RedisDataStorage.get_data_from_redis("main_session", session_id)
                if not main_session_data:
                    main_session_data = {"user_session": {}, "otp_session": {}}

                # Update the nested session data
                main_session_data[session_type] = data

                # Store the updated main_session in Redis
                await redis_client.setex(main_session_key, expiration, json.dumps(main_session_data))
                logger.info(f"✅ Updated main_session with {session_type} data for {session_id}")
            else:
                # Store other session types as separate keys
                key = f"{session_type}:{session_id}"
                await redis_client.setex(key, expiration, json.dumps(data))
                logger.info(f"✅ Data stored in Redis for {key}")
        except Exception as e:
            logger.error(f"❌ Error storing data in Redis for {session_type}:{session_id}: {e}")
            raise

    @staticmethod
    async def get_data_from_redis(session_type: str, session_id: str) -> Optional[dict]:
        """
        Retrieves data from Redis for a specific session type.
        """
        try:
            key = f"{session_type}:{session_id}"
            data = await redis_client.get(key)
            if data:
                data = json.loads(data)
                if not isinstance(data, dict):
                    logger.warning(f"⚠️ Unexpected data type in Redis for {key}: {type(data)} - Value: {data}")
                    return None
                return data
            return None
        except Exception as e:
            logger.error(f"❌ Error retrieving data from Redis for {key}: {e}")
            return None

    @staticmethod
    async def delete_data_from_redis(session_type: str, session_id: str) -> bool:
        """
        Deletes session data from Redis.
        """
        try:
            key = f"{session_type}:{session_id}"
            return await redis_client.delete(key) > 0
        except Exception as e:
            logger.error(f"❌ Error deleting data from Redis for {key}: {e}")
            return False