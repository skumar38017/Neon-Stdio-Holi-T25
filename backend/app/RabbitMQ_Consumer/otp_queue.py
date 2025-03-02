# backend/app/RabbitMQ_Consumer/otp_queue.py

import os
import sys
import logging
import asyncio
import aio_pika
from app.tasks.otp_task import send_otp_task
from app.settings import settings
from app.utils.common_icons import event_icons  # Import event icons

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Set up logging with a custom format
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def declare_queue_and_exchange(channel, queue_name, exchange_name):
    try:
        # Declare OTP Queue and Exchange
        queue = await channel.declare_queue(queue_name, durable=True)
        exchange = await channel.declare_exchange(exchange_name, aio_pika.ExchangeType.DIRECT)
        await queue.bind(exchange, routing_key=queue_name)
        logger.info(f"{event_icons['checkmark']} ✅ Declared and bound queue {queue_name} to exchange {exchange_name}")
        return queue
    except Exception as e:
        logger.error(f"{event_icons['error']} ❌ Failed to declare queue and exchange: {e}")
        raise

async def callback(message: aio_pika.IncomingMessage):
    try:
        message_body = message.body.decode()
        logger.info(f"{event_icons['info']} 📬 Received message: {message_body}")
        
        message_parts = message_body.split("|")
        if len(message_parts) not in [4, 5]:
            logger.warning(f"{event_icons['warning']} ⚠️ Skipping invalid message: {message_body}")
            await message.ack()
            return

        phone_no, name, otp, task_id, retry_flag = (message_parts + [None] * 5)[:5]
        is_retry = bool(int(retry_flag)) if retry_flag else False
        
        if phone_no is None or otp is None or task_id is None:
            logger.error(f"{event_icons['error']} ❌ Missing fields in message: {message_body}")
            await message.ack()
            return
        
        logger.info(f"{event_icons['info']} 📞 Processing OTP for {phone_no}, Name: {name}, OTP: {otp}, Task ID: {task_id}, Retry: {is_retry}")

        retry_count = 0
        max_retries = 3
        otp_delivered = False

        while retry_count < max_retries and not otp_delivered:
            retry_count += 1
            logger.info(f"{event_icons['retry']} 🔄 Attempt {retry_count}/{max_retries} for {phone_no}...")
            response = await send_otp_task(phone_no, name, otp, task_id, is_retry)

            if response.get("status") == "success":
                logger.info(f"{event_icons['checkmark']} ✅ OTP successfully delivered to {phone_no}")
                await message.ack()
                otp_delivered = True
            else:
                logger.warning(f"{event_icons['warning']} ⚠️ Failed attempt {retry_count} for {phone_no}, retrying...")
                await asyncio.sleep(2)

        if not otp_delivered:
            logger.error(f"{event_icons['error']} ❌ Failed to deliver OTP after {max_retries} attempts for {phone_no}")
            await message.ack()

    except Exception as e:
        logger.error(f"{event_icons['error']} ❌ Error processing message: {e}")
        await message.nack(requeue=True)

async def start_worker():
    try:
        connection = await aio_pika.connect_robust(host=settings.RABBITMQ_HOST)
        logger.info(f"{event_icons['checkmark']} ✅ Connected to RabbitMQ")

        async with connection:
            channel = await connection.channel()
            queues = ['otp_queue_1', 'otp_queue_2']
            exchanges = ['otp_exchange_1', 'otp_exchange_2']

            for queue_name, exchange_name in zip(queues, exchanges):
                # Declare the exchange
                exchange = await channel.declare_exchange(exchange_name, aio_pika.ExchangeType.DIRECT)
                # Declare the queue
                queue = await channel.declare_queue(queue_name, durable=True)
                # Bind the queue to the exchange
                await queue.bind(exchange, routing_key=queue_name)
                logger.info(f"{event_icons['checkmark']} ✅ Declared and bound queue {queue_name} to exchange {exchange_name}")

                # Start consuming messages
                await queue.consume(callback)
                logger.info(f"{event_icons['info']} 📬 Consuming from {queue_name}...")

            logger.info(f"{event_icons['info']} 📡 Waiting for OTP messages...")
            await asyncio.Future()  # Run forever

    except Exception as e:
        logger.error(f"{event_icons['error']} ❌ Error while connecting or consuming messages: {e}")

if __name__ == "__main__":
    asyncio.run(start_worker())
