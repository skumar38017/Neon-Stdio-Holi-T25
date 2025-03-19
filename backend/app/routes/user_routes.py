#  app/routes/user_routes.py

from fastapi import APIRouter, Depends, HTTPException, Form, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import EmailStr
from starlette.responses import JSONResponse
import logging
import time
import uuid
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
from app.utils.common_icons import event_icons

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
        try:
            # Validate phone and email
            normalized_phone_no = validate_phone(phone_no)
            normalized_email = validate_email(email)
    
            self.logger.info(f"{event_icons['user.signup']} Normalized phone: {normalized_phone_no}, email: {normalized_email}")
    
            # Generate OTP
            otp = generate_otp()
            self.logger.info(f"{event_icons['notification.new']} OTP generated: {otp}")
    
            # Generate a new session ID
            session_id = request.cookies.get("session_id") or str(uuid.uuid4())
    
            # Ensure `main_session` data is a dictionary
            main_session_data = await RedisDataStorage.get_data_from_redis("main_session", session_id)
            if not main_session_data or not isinstance(main_session_data, dict):
                main_session_data = {
                    "session_id": session_id,
                    "user_session": {},
                    "otp_session": {}
                }
                await RedisDataStorage.store_data_in_redis("main_session", session_id, main_session_data)
    
            # Store user data in `user_session`
            user_session_data = {
                "name": name,
                "email": normalized_email,
                "phone_no": normalized_phone_no,
            }
            main_session_data["user_session"] = user_session_data
            await RedisDataStorage.store_data_in_redis("main_session", session_id, main_session_data)
    
            # Store OTP in `otp_session`
            otp_expiration_time = int(time.time()) + config.otp_expiration_time['otp_expiration_time']
            otp_session_data = {
                "otp": otp,
                "otp_expiration_time": otp_expiration_time,
            }
            main_session_data["otp_session"] = otp_session_data
            await RedisDataStorage.store_data_in_redis("main_session", session_id, main_session_data)
    
            self.logger.info(f"{event_icons['redis.key.create']} Data stored in Redis for session: {session_id}")
    
            # Send OTP via SMS & Email
            phone_task_id = await self.otp_service.send_otp(phone_no=normalized_phone_no, name=name, otp=otp)
            email_task_id = await self.email_otp_service.send_email_otp(email=normalized_email, name=name, otp=otp)
    
            return JSONResponse(
                content={
                    "message": f"{event_icons['notification.new']} OTP sent and user data stored temporarily.",
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
        request: Request,
        otp: str = Form(..., description="OTP entered by the user"),
        db: AsyncSession = Depends(get_db),
    ) -> JSONResponse:
        """
        Verify the OTP and proceed with user registration.
        """
        try:
            # Retrieve session ID from cookies
            session_id = request.cookies.get("session_id", None)
            self.logger.info(f"🔍 Checking OTP for session_id: {session_id}")

            if not session_id:
                self.logger.error("❌ Session ID missing in cookies. Verification failed.")
                raise HTTPException(status_code=401, detail="Session expired or invalid.")

            # Verify OTP
            user_data = await verify_otp(session_id, otp)

            if not user_data:
                self.logger.warning("⚠️ Invalid or expired OTP.")
                raise HTTPException(status_code=400, detail="Invalid or expired OTP.")

            # Proceed to user creation
            user_create = UserCreate(**user_data)
            user_response = await self.user_crud.create_user(db, user_create)

            # Cleanup session data
            main_session_data = await RedisDataStorage.get_data_from_redis("main_session", session_id)
            if main_session_data:
                main_session_data.pop("otp_session", None)
                main_session_data.pop("user_session", None)
                await RedisDataStorage.store_data_in_redis("main_session", session_id, main_session_data)

            self.logger.info(f"✅ User registered successfully: {user_response}")

            return JSONResponse(
                content={
                    "message": "✅ User registered successfully",
                    "user_data": {
                        **user_response.model_dump(),
                        "created_at": user_response.created_at.isoformat(),
                        "updated_at": user_response.updated_at.isoformat()
                    }
                }
            )

        except HTTPException as e:
            raise e
        except Exception as e:
            self.logger.error(f"❌ Error verifying OTP: {str(e)}")
            raise HTTPException(status_code=500, detail="Error verifying OTP")

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