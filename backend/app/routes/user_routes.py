#  app/routes/user_routes.py

from fastapi import APIRouter, Depends, HTTPException, Form, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import EmailStr
from starlette.responses import JSONResponse
import logging
import os
from app.database.database import get_db
from app.schemas import UserCreate, UserResponse, VerifyOTPResponse
from app.config import config
from app.utils.redis_data_storage import RedisDataStorage
from app.curd_operation.user_curd import UserCRUD
from app.services.otp_service import OTPService
from app.services.email_otp_service import EmailOTPService
from app.utils.generate_otp import generate_otp
from app.utils.otp_verification import verify_otp
from app.utils.validator import validate_phone
from app.utils.validate_email import validate_email
from app.utils.common_icons import event_icons  # Import event icons for easy access

class UserRoutes:
    def __init__(self):
        self.router = APIRouter()
        self.otp_service = OTPService()
        self.email_otp_service = EmailOTPService()
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
            response_model=VerifyOTPResponse,
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
        name: str = Form(...),
        email: EmailStr = Form(...),
        phone_no: str = Form(...),
        db: AsyncSession = Depends(get_db),
    ) -> JSONResponse:
        """
        Handle user registration via a form in the browser.
        """
        try:
            # Step 1: Validate and normalize phone number
            normalized_phone_no = validate_phone(phone_no)
            self.logger.info(f"{event_icons['user.signup']} Normalized phone number: {normalized_phone_no}")

            # Step 2: Validate and normalize email
            normalized_email = validate_email(email)
            self.logger.info(f"{event_icons['user.signup']} Normalized email: {normalized_email}")

            # Step 3: Generate OTP
            otp = generate_otp()
            self.logger.info(f"{event_icons['notification.new']} OTP generated for user: {otp}")

            # Step 4: Manage session
            session_id = request.cookies.get("session_id", None)  # Check for session_id in cookies
            if not session_id:  # If no session_id, create a new one
                session_id = os.urandom(24).hex()
                request.state.session = {"session_id": session_id}
            else:
                self.logger.info(f"{event_icons['user.logged_in']} Using existing session_id: {session_id}")

            # Step 5: Store data in Redis using the session_id as the key
            redis_data = {
                "name": name,
                "email": normalized_email,
                "phone_no": normalized_phone_no,
                "otp": otp,
                "otp_expiration_time": config.otp_expiration_time
            }
            RedisDataStorage.store_data_in_redis(
                session_id,
                redis_data,
                expiration=config.expiration_time,
            )
            self.logger.info(f"{event_icons['redis.key.create']} Data stored in Redis for session: {session_id}")

            # Step 6: Trigger OTP task asynchronously using OTPService
            phone_task_id = await self.otp_service.send_otp(phone_no=normalized_phone_no, name=name, otp=otp)
            email_task_id = await self.email_otp_service.send_email_otp(email=normalized_email, name=name, otp=otp)
            self.logger.info(f"{event_icons['otpVerify']} Phone OTP task ID: {phone_task_id}, Email OTP task ID: {email_task_id}")

            # Step 7: Respond with task information and session data
            return JSONResponse(
                content={
                    "message": f"{event_icons['notification.new']} OTP sent and user data stored temporarily in Redis.",
                    "session_id": session_id,
                    "phone_task_id": phone_task_id,
                    "email_task_id": email_task_id
                },
                headers={"Set-Cookie": f"session_id={session_id}; HttpOnly"},
            )

        except Exception as e:
            self.logger.error(f"{event_icons['system.error']} Error during user registration: {str(e)}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred.")
    
    async def verify_otp_route(
        self,
        request: Request,  # To access session data
        otp: str = Form(..., description="OTP entered by the user"),
        db: AsyncSession = Depends(get_db),
    ) -> JSONResponse:
        """
        Verify the OTP and proceed with user registration.
        """
        try:
            # Step 1: Get user session ID from cookies (or request state if you use it)
            session_id = request.cookies.get("session_id", None)  # Check for session ID in cookies
            self.logger.info(f"{event_icons['user.logged_in']} Session ID from cookies: {session_id}")
            if not session_id:
                raise HTTPException(status_code=401, detail="Session expired or invalid.")
            
            # Step 2: Verify OTP using the redis_key (session_id)
            user_data = await verify_otp(session_id, otp)  # Call the OTP verification function
            if not user_data:
                self.logger.warning(f"{event_icons['notification.read']} Invalid or expired OTP.")
                raise HTTPException(status_code=400, detail="Invalid or expired OTP.")

            # Step 3: Proceed to user creation
            user_create = UserCreate(**user_data)  # Assuming user_data contains the necessary fields
            user_response = await self.user_crud.create_user(db, user_create)

            # Step 4: Return success response
            self.logger.info(f"{event_icons['user.created']} User registered successfully: {user_response}")
            return JSONResponse(
                content={
                    "message": f"{event_icons['user.created']} User registered successfully",
                    "user_data": {
                        **user_response.model_dump(),
                        "created_at": user_response.created_at.isoformat(),
                        "updated_at": user_response.updated_at.isoformat()
                    }
                }
            )

        except HTTPException as e:
            raise e  # Re-raise HTTPExceptions directly
        except Exception as e:
            # Log the exception and raise a general HTTP error
            self.logger.error(f"{event_icons['system.error']} Error verifying OTP: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error verifying OTP: {str(e)}")
                
    async def get_user_route(self, uuid: str, db: AsyncSession = Depends(get_db)) -> UserResponse:
        """
        Retrieve a user by UUID.
        """
        try:
            user = await self.user_crud.get_user_by_uuid(uuid, db)
            if not user:
                self.logger.warning(f"{event_icons['user.get']} User not found: {uuid}")
                raise HTTPException(status_code=404, detail="User not found")
            self.logger.info(f"{event_icons['user.get']} Retrieved user: {uuid}")
            return user
        except Exception as e:
            self.logger.error(f"{event_icons['system.error']} Error retrieving user: {str(e)}")
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
                self.logger.warning(f"{event_icons['user.update']} User update failed: {uuid}")
                raise HTTPException(status_code=404, detail="User not found or update failed")
            self.logger.info(f"{event_icons['user.update']} User updated successfully: {uuid}")
            return updated_user
        except Exception as e:
            self.logger.error(f"{event_icons['system.error']} Error updating user: {str(e)}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred.")

    async def delete_user_route(self, uuid: str, db: AsyncSession = Depends(get_db)) -> dict:
        """
        Delete a user by UUID.
        """
        try:
            deleted = await self.user_crud.delete_user(uuid, db)
            if not deleted:
                self.logger.warning(f"{event_icons['user.delete']} User deletion failed: {uuid}")
                raise HTTPException(status_code=404, detail="User not found or deletion failed")
            self.logger.info(f"{event_icons['user.delete']} User deleted successfully: {uuid}")
            return {"message": f"{event_icons['user.delete']} User deleted successfully"}
        except Exception as e:
            self.logger.error(f"{event_icons['system.error']} Error deleting user: {str(e)}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred.")


# Create an instance of the class and expose its router
user_routes = UserRoutes()
router = user_routes.router
