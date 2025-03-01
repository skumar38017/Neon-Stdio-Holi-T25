# app/routes/user_routes.py

from fastapi import APIRouter, Depends, HTTPException, Form, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import EmailStr
from starlette.responses import JSONResponse
import logging
import os
import pika  # Import pika for RabbitMQ
from app.database.database import get_db
from app.schemas import UserCreate, UserResponse
from app.config import config
from app.utils.redis_data_storage import RedisDataStorage
from app.curd_operation.user_curd import UserCRUD
from app.services.otp_service import OTPService
from app.services.email_otp_service import EmailOTPService
from app.utils.generate_otp import generate_otp
from app.utils.otp_verification import verify_otp
from app.utils.validator import validate_phone
from app.utils.validate_email import validate_email


class UserRoutes:
    def __init__(self):
        self.router = APIRouter()
        self.otp_service = OTPService()  # Correct reference to OTPService
        self.email_otp_service = EmailOTPService()  # Correct reference to EmailOTPService
        self.user_crud = UserCRUD()
        self.redis_data_storage = RedisDataStorage()
        self.logger = logging.getLogger("uvicorn.error")
        self._setup_routes()

    def _setup_routes(self):
        """
        Registers all routes in the APIRouter.
        """
        self.router.post(
            "/register",
            response_model=UserResponse,
            status_code=201,
            description="Create a new user for the ticketing system and store user information in the database",
        )(self.create_user_route)

        self.router.post(
            "/otpVerify",
            response_model=UserResponse,
            status_code=200,
            description="Verify otp and send the user details into the response."
        )(self.verify_otp_route)

        self.router.get(
            "/user/{uuid}",
            response_model=UserResponse,
            description="Retrieve a user by UUID"
        )(self.get_user_route)

        self.router.put(
            "/user/{uuid}",
            response_model=UserResponse,
            description="Update a user by UUID"
        )(self.update_user_route)

        self.router.delete(
            "/user/{uuid}",
            response_model=dict,
            description="Delete a user by UUID"
        )(self.delete_user_route)

    async def create_user_route(
        self,
        request: Request,
        name: str = Form(..., description="Name of the user `Admin`"),
        email: EmailStr = Form(..., description="Valid email address of the user `admin@admin.com`"),
        phone_no: str = Form(..., description="Phone number of the user ``+919876543210` | `919876543210` | `9876543210` | `+91-98765 43210`"),
        db: AsyncSession = Depends(get_db),
    ) -> JSONResponse:
        """
        Handle user registration via a form in the browser.
        """
        try:
            # Step 1: Validate and normalize phone number
            normalized_phone_no = validate_phone(phone_no)
            self.logger.info(f"Normalized phone number: {normalized_phone_no}")

            # Step 2: Validate and normalize email
            normalized_email = validate_email(email)
            self.logger.info(f"Normalized email: {normalized_email}")

            # Step 2: Prepare user data
            user_data = {"name": name, "email": normalized_email, "phone_no": normalized_phone_no}

            # Step 3: Generate OTP
            otp = generate_otp()

            # Step 4: Manage session
            session = getattr(request.state, "session", None)
            if session is None or "session_id" not in session:
                session_id = os.urandom(24).hex()
                request.state.session = {"session_id": session_id}
            else:
                session_id = session["session_id"]

            # Step 5: Generate Redis key
            redis_key = RedisDataStorage.generate_redis_key(name=name, email=normalized_email, phone_no=normalized_phone_no)

            # Step 6: Store data in Redis
            redis_data = {
                "name": name,
                "email": normalized_email,
                "phone_no": normalized_phone_no,
                "otp": otp,
            }
            RedisDataStorage.store_data_in_redis(
                redis_key,
                redis_data,
                session_id=session_id,
                expiration=config.expiration_time,
            )

            # Step 7: Trigger OTP task asynchronously using OTPService
            task_id = await self.otp_service.send_otp(phone_no=normalized_phone_no, name=name, otp=otp)
            task_id = await self.email_otp_service.send_email_otp(email=normalized_email, name=name, otp=otp)
            
            self.logger.info(f"OTP generated for {normalized_phone_no}, Phone_OTP task_id: {task_id}")
            self.logger.info(f"OTP generated for {normalized_email}, Email_OTP task_id: {task_id}")

            # Step 9: Respond with task information
            return JSONResponse(
                content={
                    "message": "OTP sent and user data stored temporarily in Redis.",
                    "phone_no": redis_key,
                    "task_id": task_id,
                },
                headers={"Set-Cookie": f"session_id={session_id}; HttpOnly"},
            )

        except Exception as e:
            self.logger.error(f"Error during user registration: {str(e)}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred.")
        
    async def verify_otp_route(
        self,
        redis_key: str = Form(..., description="Redis key storing OTP"),
        otp: str = Form(..., description="OTP entered by the user"),
        db: AsyncSession = Depends(get_db),
    ) -> JSONResponse:
        """
        Verify the OTP and register the user if the OTP is valid.
        """
        try:
            # Step 1: Verify the OTP
            user_data = await verify_otp(redis_key, otp)
            print('user_data', user_data)

            if not user_data:
                raise HTTPException(status_code=400, detail="Invalid or expired OTP.")
            
            # Step 2: Remove session data from user_data
            user_data.pop('session', None)

            # Step 3: Convert user_data to UserCreate schema
            user_create = UserCreate(
                name=user_data['name'],
                email=user_data['email'],
                phone_no=user_data['phone_no']
            )

            # Step 4: Save user data to the database using UserCRUD
            user_response = await self.user_crud.create_user(db, user_create)

            # Step 5: Return success response with user data
            return JSONResponse(
                content={
                    "message": "User registered successfully",
                    "user_data": {
                        **user_response.model_dump(),
                        "created_at": user_response.created_at.isoformat(),  # Convert datetime to string
                        "updated_at": user_response.updated_at.isoformat()   # Convert datetime to string
                    }
                }
            )

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error verifying OTP: {str(e)}")
            
    async def get_user_route(self, uuid: str, db: AsyncSession = Depends(get_db)) -> UserResponse:
        """
        Retrieve a user by UUID.
        """
        try:
            user = await self.user_crud.get_user_by_uuid(uuid, db)
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            return user
        except Exception as e:
            self.logger.error(f"Error retrieving user: {str(e)}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred.")

    async def update_user_route(
        self, uuid: str, user_data: UserCreate, db: AsyncSession = Depends(get_db)
    ) -> UserResponse:
        """
        Update a user by UUID.
        """
        try:
            updated_user = await self.user_crud.update_user(uuid, user_data, db)
            if not updated_user:
                raise HTTPException(status_code=404, detail="User not found or update failed")
            return updated_user
        except Exception as e:
            self.logger.error(f"Error updating user: {str(e)}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred.")

    async def delete_user_route(self, uuid: str, db: AsyncSession = Depends(get_db)) -> dict:
        """
        Delete a user by UUID.
        """
        try:
            deleted = await self.user_crud.delete_user(uuid, db)
            if not deleted:
                raise HTTPException(status_code=404, detail="User not found or deletion failed")
            return {"message": "User deleted successfully"}
        except Exception as e:
            self.logger.error(f"Error deleting user: {str(e)}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred.")


# Create an instance of the class and expose its router
user_routes = UserRoutes()
router = user_routes.router