#  app/services/email_otp_service.py

import logging
import uuid
import asyncio
from fastapi import HTTPException
from app.config import config
from app.services.websocket_service import WebSocketHandler
from app.database.redisclient import redis_client
from app.settings import settings
import aio_pika

class EmailOTPService:
    def __init__(self):
        self.logger = logging.getLogger("uvicorn.error")
        self.redis_client = redis_client
        self.websocket_handler = WebSocketHandler()

    async def send_email_otp(self, email: str, name: str, otp: str) -> str:
        try:
            await self.websocket_handler.send_task_status(email, "queued")
            task_id = str(uuid.uuid4())
            retry_attempts = int(await self.redis_client.get(f"email_otp_retry_{email}") or 0)
            is_retry = retry_attempts > 0
            await self._send_email_otp_to_rabbitmq(email, name, otp, task_id, is_retry)
            self.logger.info(f"Email OTP task queued with ID {task_id} for email {email}")
            asyncio.create_task(self._track_task_status(task_id, email, otp))
            return task_id
        except Exception as e:
            self.logger.error(f"Error sending Email OTP: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to send Email OTP.")

    async def _track_task_status(self, task_id: str, email: str, otp: str):
        attempts = int(await self.redis_client.get(f"email_otp_retry_{email}") or 0)
        try:
            await asyncio.sleep(2)
            await self.websocket_handler.send_task_status(email, "processing")
            if attempts < 2:
                if await self._send_email_otp(email, otp):
                    await self.websocket_handler.send_task_status(email, "success")
                    self.logger.info(f"Task {task_id} completed successfully.")
                else:
                    attempts += 1
                    self.redis_client.setex(f"email_otp_retry_{email}", config.otp_expiration_time['otp_expiration_time'], attempts)
                    await self.websocket_handler.send_task_status(email, f"retrying attempt {attempts}")
                    await self._track_task_status(task_id, email, otp)
            else:
                await self.websocket_handler.send_task_status(email, "failed")
                self.logger.error(f"Task {task_id} failed after 3 attempts.")
        except Exception as e:
            self.logger.error(f"Error tracking task {task_id}: {str(e)}")
            await self.websocket_handler.send_task_status(email, "failed")

    async def _send_email_otp(self, email: str, otp: str) -> bool:
        try:
            success = True
            if not success:
                return False
            return True
        except Exception as e:
            self.logger.error(f"Error sending OTP to {email}: {str(e)}")
            return False

    async def _send_email_otp_to_rabbitmq(self, email: str, name: str, otp: str, task_id: str, is_retry: bool = False):
        try:
            if any(x is None for x in [email, name, otp, task_id]):
                raise ValueError("One or more required fields are missing.")
            selected_queue = 'email_otp_queue_2' if is_retry else 'email_otp_queue_1'
            message_body = f"{email}|{name}|{otp}|{task_id}|{int(is_retry)}"
            connection = await aio_pika.connect_robust(host=settings.RABBITMQ_HOST)
            async with connection:
                channel = await connection.channel()
                await channel.declare_queue(selected_queue, durable=True)
                message = aio_pika.Message(body=message_body.encode(), delivery_mode=aio_pika.DeliveryMode.PERSISTENT)
                await channel.default_exchange.publish(message, routing_key=selected_queue)
                self.logger.info(f"Sent Email OTP task to RabbitMQ for email {email} on queue {selected_queue}")
        except ValueError as ve:
            self.logger.error(f"Error: {str(ve)}")
            raise HTTPException(status_code=400, detail="Invalid input values.")
        except Exception as e:
            self.logger.error(f"Error sending Email OTP task to RabbitMQ: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to send Email OTP task to RabbitMQ.")