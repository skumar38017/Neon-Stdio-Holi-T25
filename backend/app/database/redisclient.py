# app/database/redisclient.py
# app/database/redisclient.py
import redis.asyncio as aioredis
import logging
from app.config import config
from app.utils.common_icons import event_icons  # Import event icons

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RedisClient:
    def __init__(self):
        """
        Initialize Redis client with the broker URL from the configuration.
        """
        self.redis = None

    async def connect(self):
        """
        Connect to Redis asynchronously and test the connection.
        """
        try:
            self.redis = await aioredis.from_url(config.redis_result_url, decode_responses=True)
            await self.redis.ping()
            logger.info(f"{event_icons['checkmark']} ✅ Successfully connected to Redis. Redis host: {config.redis_result_url}")
            print(f"✅ Successfully connected to Redis. Redis host: {config.redis_result_url}")
        except Exception as e:
            logger.error(f"{event_icons['error']} ❌ Failed to connect to Redis: {e}")
            raise

    async def setex(self, name, time, value):
        """
        Set the value of a key with an expiration time asynchronously.
        """
        try:
            await self.redis.setex(name, time, value)
            logger.info(f"{event_icons['set']} Set key {name} with expiration time {time}.")
            print(f"Set key {name} with expiration time {time}.")
        except Exception as e:
            logger.error(f"{event_icons['error']} ❌ Error setting key {name}: {e}")
            raise

    async def get(self, name):
        """
        Get the value of a key asynchronously.
        """
        try:
            result = await self.redis.get(name)
            logger.info(f"{event_icons['get']} Retrieved value for key {name}.")
            print(f"Retrieved value for key {name}.")
            return result
        except Exception as e:
            logger.error(f"{event_icons['error']} ❌ Error getting key {name}: {e}")
            raise

    async def execute_command(self, *args, **kwargs):
        """
        Execute a Redis command asynchronously.
        """
        try:
            result = await self.redis.execute_command(*args, **kwargs)
            logger.info(f"{event_icons['command']} Executed Redis command: {args[0]}")
            print(f"Executed Redis command: {args[0]}")
            return result
        except Exception as e:
            logger.error(f"{event_icons['error']} ❌ Error executing Redis command {args[0]}: {e}")
            raise

    async def disconnect(self):
        """
        Disconnect from Redis gracefully.
        """
        try:
            await self.redis.close()
            logger.info(f"{event_icons['disconnect']} Disconnected from Redis.")
            print(f"Disconnected from Redis.")
        except Exception as e:
            logger.error(f"{event_icons['error']} ❌ Error disconnecting from Redis: {e}")
            raise

    async def get_redis_status(self):
        """
        Fetch and print Redis server status asynchronously.
        """
        try:
            info = await self.redis.info()
            logger.info(f"{event_icons['info']} Redis Server Information: {info}")
            print("Redis Server Information:")
            for key, value in info.items():
                print(f"{key}: {value}")
        except Exception as e:
            logger.error(f"{event_icons['error']} ❌ Error fetching Redis status: {e}")
            raise

    async def get_active_clients(self):
        """
        Fetch and print active Redis clients asynchronously.
        """
        try:
            clients = await self.redis.client_list()
            logger.info(f"{event_icons['user']} Active Redis Clients: {clients}")
            print("Active Redis Clients:")
            for client in clients:
                print(client)
        except Exception as e:
            logger.error(f"{event_icons['error']} ❌ Error fetching active Redis clients: {e}")
            raise

# Create a RedisClient instance
redis_client = RedisClient()
