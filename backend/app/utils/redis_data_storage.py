# app/utils/redis_data_storage.py

import json
import hashlib
from typing import Optional
from app.database.redisclient import redis_client  # Import the redis_client instance
from app.config import config


class RedisDataStorage:
    """
    A class to handle Redis data storage operations, including hashing and session management.
    """

    @staticmethod
    def hash_data(data: str) -> str:
        """
        Hash the input data using SHA-256.

        Args:
            data (str): The data to hash.

        Returns:
            str: The hashed value as a hexadecimal string.
        """
        return hashlib.sha256(data.encode()).hexdigest()

    @staticmethod
    def generate_redis_key(name: str, email: str, phone_no: str) -> str:
        """
        Generate a unique Redis key by hashing the combination of name, email, and phone number.

        Args:
            name (str): The name of the user.
            email (str): The email of the user.
            phone_no (str): The phone number of the user.

        Returns:
            str: The generated Redis key.
        """
        combined_data = f"{name}_{email}_{phone_no}"
        return f"{phone_no}:{RedisDataStorage.hash_data(combined_data)}"

    @staticmethod
    def store_data_in_redis(key: str, data: dict, session_id: str, expiration: int = config.expiration_time) -> None:
        """
        Store hashed data in Redis with an expiration time and session information.
        """
        try:
            data_with_session = {**data, "session": session_id}
            combined_data = json.dumps(data_with_session)
            hashed_data = RedisDataStorage.hash_data(combined_data)

            redis_client.setex(
                key, expiration, json.dumps({"original_data": data_with_session, "hashed_data": hashed_data})
            )
        except Exception as e:
            print(f"Error storing data in Redis: {e}")
            raise

    @staticmethod
    def get_data_from_redis(key: str) -> Optional[dict]:
        """
        Retrieve data from Redis using the key.
        """
        try:
            data = redis_client.get(key)
            if data:
                stored_data = json.loads(data.decode())
                original_data = stored_data.get("original_data")
                hashed_data = stored_data.get("hashed_data")

                if RedisDataStorage.hash_data(json.dumps(original_data)) == hashed_data:
                    return original_data  # Return the original data if the hash matches
                else:
                    print("Data integrity check failed: Hash mismatch")
                    return None
            return None
        except Exception as e:
            print(f"Error retrieving data from Redis: {e}")
            return None

    @staticmethod
    def delete_data_from_redis(key: str) -> bool:
        """
        Delete data from Redis using the key.
        """
        try:
            result = redis_client.delete(key)
            return result > 0
        except Exception as e:
            print(f"Error deleting data from Redis for key {key}: {e}")
            return False

    @staticmethod
    def get_redis_key_by_session(session_id: str) -> Optional[str]:
        """
        Retrieve the Redis key associated with a session.
        """
        try:
            redis_keys = redis_client.keys("*")
            for key in redis_keys:
                data = redis_client.get(key)
                if data:
                    parsed_data = json.loads(data)
                    if parsed_data.get("original_data", {}).get("session") == session_id:
                        return key.decode()
            return None
        except Exception as e:
            print(f"Error fetching redis key: {e}")
            return None
