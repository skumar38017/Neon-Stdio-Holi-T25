#  app/routes/user_routes.py

from fastapi import APIRouter, HTTPException
from app.tasks.otp_task import send_otp_task
from app.tasks.payment_task import process_payment_task
from app.tasks.qr_task import generate_qr_task

from fastapi import APIRouter, Depends
from app.services.websocket_service import WebSocketHandler
from app.services.otp_service import send_otp
from app.utils.qr_generator import generate_qr_code
from app.utils.email_utils import send_email

from fastapi import APIRouter
from app.tasks.otp_task import send_otp_task
from app.tasks.payment_task import process_payment_task
from app.tasks.qr_task import generate_qr_task
from app.tasks.email_tasks import send_welcome_email

router = APIRouter()

@router.post("/get_users", response_model=schemas.UserResponse,
            operation_id="get_users",
            summary="Get all users",
            description="Get all users from the database.",
)
async def get_users(
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get all users from the database.
    Args:
        db (AsyncSession, optional): _description_. Defaults to Depends(get_db).
    Returns:
        JSONResponse: _description_
    """
    logger.info(
        f"Received request to get all users from the database."
    )

    return JSONResponse(
        status_code=200,
        content=await db.execute(
            select(User).where(User.is_active == True)
        ),
        headers={"Content-Type": "application/json"},
    )


@router.post("/register",response_model=schemas.UserResponse)
async def register(
                      user_id: uuid.UUID = Form(...),
                      user_name: str = Form(...),
                      mobile_no: str = Form(...),
                      email: str = Form(...),
                      ticket_type: str = Form(...),
                      ticket_price: float = Form(...),
                      db: AsyncSession = Depends(get_db),
                      )-> JSONResponse:
    # Book ticket logic
    # Assuming ticket booking is successful
    return {"message": "Ticket booked successfully"}
    # Trigger OTP task
    send_otp_task.delay(user_data["mobile_no"])
    return {"message": "OTP sent to your mobile number"}


@router.post("/verify_otp", response_model=schemas.UserResponse)
async def verify_otp(mobile_no: str, otp: str):
    # OTP verification logic (can also be handled in Celery)
    # Assuming OTP is valid for now
    return {"message": "OTP verified"}

@router.get("/process-payment/")
async def trigger_payment(payment_data: dict):
    result = process_payment_task.delay(payment_data)
    return {"task_id": result.id, "status": "Payment Task Sent"}

@router.get("/generate-qr/")
async def trigger_qr(data: dict):
    result = generate_qr_task.delay(data)
    return {"task_id": result.id, "status": "QR Task Sent"}


@router.get("/success")
async def success_page():
    return JSONResponse(content={"message": "QR Code validated successfully. Welcome!"})

@router.get("/error")
async def error_page():
    return JSONResponse(content={"message": "Invalid QR Code. Please try again."})


@router.post("/validate_qr",
             status_code=200,
             response_model=schemas.UserResponse,
             response_model_exclude_none=True,
             response_model_exclude_unset=True,
             tags=["User"],
             summary="Validate QR code",
             description="Validate QR code and return user details.",
             )
async def validate_qr(file: UploadFile, db: AsyncSession = Depends(get_db)):
    try:
        # Open the uploaded file as an image
        img = Image.open(file.file)
        
        # Decode the QR code from the image
        decoded_data = decode(img)
        if not decoded_data:
            raise HTTPException(status_code=400, detail="No QR code found in the image.")
        
        # Decode QR code data to JSON
        qr_data = decoded_data[0].data.decode('utf-8')
        user_data = json.loads(qr_data)
        
        # Validate the user from database (can be replaced with custom logic)
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email=%s", (user_data["email"],))
        user = cursor.fetchone()
        conn.close()

        if user:
            return RedirectResponse(url="/success", status_code=303)
        else:
            raise HTTPException(status_code=400, detail="Invalid QR code or user not found.")
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error: {str(e)}")


@router.get("/generate_otp")
async def trigger_otp(mobile_no: str, ticket_price: float, ticket_name: str, ticket_qty: int):
    result = send_otp_task.delay(mobile_no, ticket_price, ticket_name, ticket_qty)
    return {"task_id": result.id, "status": "OTP Task Sent"}