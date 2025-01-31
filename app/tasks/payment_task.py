# app/tasks/payment_task.py
from app.workers.celery_app import celery_app
from app.services.payment_service import process_payment

@celery_app.task
def process_payment_task(payment_data: dict):
    """
    Processes the payment in the background.
    
    Args:
        payment_data (dict): The data associated with the payment.
    """
    result = process_payment(payment_data)
    return result
