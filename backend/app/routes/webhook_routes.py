# app/routes/webhook_routes.py

from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database.database import get_db  # Ensure correct import path
from app.database.models import Payment, Order
from app.utils.common_icons import event_icons  # Importing the icons
import razorpay
import json
import hashlib
import logging
from app.config import config

# Configure logging
logger = logging.getLogger("uvicorn.error")

# Initialize Razorpay client
client = razorpay.Client(auth=(config.razorpay_key["key"], config.razorpay_key["secret"]))

# Webhook Router
webhook_router = APIRouter()

@webhook_router.post("/webhook/payment")
async def razorpay_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Webhook endpoint to handle Razorpay events.
    """
    payload = await request.body()  # Get raw payload
    sig_header = request.headers.get("X-Razorpay-Signature")  # Razorpay signature header

    # Compute the HMAC hash using the webhook secret
    secret = config.razorpay_webhook_secret  # Webhook secret
    generated_signature = hashlib.sha256(payload).hexdigest()

    # Verify the signature to ensure it came from Razorpay
    if not razorpay.utils.verify_webhook_signature(payload, sig_header, secret):
        logger.error(f"{event_icons['error']} ❌ Invalid webhook signature")
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    # Parse the webhook data
    webhook_data = json.loads(payload.decode())
    event = webhook_data.get("event")
    logger.info(f"{event_icons.get(event, '⚠️')} 📬 Received Razorpay event: {event}")

    try:
        # Handle payment events
        if event == "payment.authorized":
            # Handle payment authorization
            logger.info(f"{event_icons.get(event, '✅')} Payment authorized: {webhook_data}")
            # Add your logic here (e.g. mark payment as authorized in your DB)

        elif event == "payment.failed":
            # Handle payment failure
            logger.error(f"{event_icons.get(event, '❌')} Payment failed: {webhook_data}")
            # Add your logic here (e.g. mark payment as failed in your DB)

        elif event == "payment.captured":
            # Handle payment captured
            transaction_id = webhook_data["payload"]["payment"]["entity"]["id"]
            result = await db.execute(select(Payment).where(Payment.transaction_id == transaction_id))
            payment_record = result.scalars().first()

            if payment_record:
                payment_record.transaction_status = "captured"
                await db.commit()
                logger.info(f"{event_icons.get(event, '✅')} Payment {transaction_id} captured.")
            else:
                logger.warning(f"{event_icons.get(event, '⚠️')} No payment found for transaction ID: {transaction_id}")

        # Handle other events similarly by checking the event type
        elif event == "order.paid":
            # Handle order paid
            logger.info(f"{event_icons.get(event, '✅')} Order paid: {webhook_data}")
            # Add your logic here to update the order status

        elif event == "refund.processed":
            # Handle refund processed
            logger.info(f"{event_icons.get(event, '✅')} Refund processed: {webhook_data}")

        # Default case for unhandled events
        else:
            logger.warning(f"{event_icons.get(event, '⚠️')} Unhandled event: {event}")

        # Return a success response to Razorpay
        return JSONResponse(status_code=200, content={"message": "Event received successfully"})

    except Exception as e:
        logger.error(f"{event_icons['error']} ❌ Error handling webhook event: {e}")
        return JSONResponse(status_code=500, content={"message": "Internal server error"})

# Export the router
__all__ = ["webhook_router"]
