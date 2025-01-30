# app/routes/user_routes.py

from fastapi import APIRouter, Depends, HTTPException, Form, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import EmailStr
from starlette.responses import JSONResponse
import logging
import os

from app.database.database import get_db
from app.schemas import UserCreate, UserResponse
from app.config import config
from app.utils.redis_data_storage import RedisDataStorage
from app.curd_operation.user_curd import UserCRUD


class UserRoutes:
    def __init__(self):
        self.router = APIRouter()
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
            description="Create a new user for the ticketing system and store user information in the database"
        )(self.create_user_route)

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
        self,  # Add `self` as the first parameter
        request: Request,
        name: str = Form(..., description="Name of the user `admin`"),
        email: EmailStr = Form(..., description="Valid email address of the user `admin@admin.com`"),
        phone_no: str = Form(..., description="Phone number of the user `91 99999 99999` or `+91-99999 99999`"),
        is_active: bool = Form(True, description="User status, active or not"),
        db: AsyncSession = Depends(get_db),
    ) -> JSONResponse:
        """
        Handle user registration via a form in the browser.
        """
        try:
            # Create a Pydantic UserCreate model
            user_data = UserCreate(
                name=name,
                email=email,
                phone_no=phone_no,
                is_active=is_active,
            )

            # Generate a unique Redis key
            redis_key = self.redis_data_storage.generate_redis_key(name, email, phone_no)

            # Generate or retrieve session information
            session = getattr(request.state, "session", None)
            if session is None or "session_id" not in session:
                session = {"session_id": os.urandom(24).hex()}
                request.state.session = session

            # Store the data in Redis with the session ID
            self.redis_data_storage.store_data_in_redis(
                redis_key,
                user_data.model_dump(),  # Convert Pydantic model to dictionary
                session_id=session["session_id"],  # Use session_id directly
                expiration=config.expiration_time
            )

            # Log the event
            self.logger.info(f"User data temporarily stored in Redis for key: {redis_key} {user_data}")

            # Respond back with success message
            return JSONResponse(
                content={"message": f"User data stored temporarily in Redis. key: {redis_key} {user_data}"},
                headers={"Set-Cookie": f"session_id={session['session_id']}; HttpOnly"}  # Set the session cookie
            )

        except Exception as e:
            self.logger.error(f"Exception during user registration: {str(e)}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred.")

    async def get_user_route(self, uuid: str, db: AsyncSession = Depends(get_db)) -> UserResponse:
        """
        Retrieve a user by UUID.
        """
        try:
            user = await self.user_crud.get_user_by_uuid(db=db, uuid=uuid)
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            return user
        except Exception as e:
            self.logger.error(f"Exception retrieving user with UUID {uuid}: {str(e)}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred.")

    async def update_user_route(self, uuid: str, user: UserCreate, db: AsyncSession = Depends(get_db)) -> UserResponse:
        """
        Update a user by UUID.
        """
        try:
            updated_user = await self.user_crud.update_user(db=db, uuid=uuid, user=user)
            if not updated_user:
                raise HTTPException(status_code=404, detail="User not found")
            return updated_user
        except Exception as e:
            self.logger.error(f"Exception updating user with UUID {uuid}: {str(e)}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred.")

    async def delete_user_route(self, uuid: str, db: AsyncSession = Depends(get_db)) -> dict:
        """
        Delete a user by UUID.
        """
        try:
            success = await self.user_crud.delete_user(db=db, uuid=uuid)
            if not success:
                raise HTTPException(status_code=404, detail="User not found")
            return {"message": "User deleted successfully"}
        except Exception as e:
            self.logger.error(f"Exception deleting user with UUID {uuid}: {str(e)}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred.")


# Create an instance of the class and expose its router
user_routes = UserRoutes()
router = user_routes.router