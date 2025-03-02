# app/utils/redis_data_storage.py

import json
import hashlib
from typing import Optional
from app.database.redisclient import redis_client  # Import the redis_client instance
from app.config import config


class RedisDataStorage:
    """
    A class to handle Redis data storage operations, storing all user data under session ID.
    """
    @staticmethod
    def store_data_in_redis(session_id: str, data: dict, expiration: int = config.expiration_time) -> None:
        """
        Store user data in Redis using the session ID as the key.
        """
        try:
            # Include session ID and OTP in the data
            data_with_session = {**data, "session_id": session_id}
            # Store the data under the session ID key
            redis_client.setex(session_id, expiration, json.dumps(data_with_session))
        except Exception as e:
            print(f"Error storing data in Redis: {e}")
            raise

    @staticmethod
    def get_data_from_redis(session_id: str) -> Optional[dict]:
        """
        Retrieve data from Redis using the session ID.
        """
        try:
            data = redis_client.get(session_id)
            if data:
                # If data exists, return it as a JSON object
                return json.loads(data.decode())
            return None
        except Exception as e:
            print(f"Error retrieving data from Redis: {e}")
            return None

    @staticmethod
    def delete_data_from_redis(session_id: str) -> bool:
        """
        Delete user data from Redis using the session ID.
        """
        try:
            result = redis_client.delete(session_id)
            return result > 0
        except Exception as e:
            print(f"Error deleting data from Redis for session {session_id}: {e}")
            return False
