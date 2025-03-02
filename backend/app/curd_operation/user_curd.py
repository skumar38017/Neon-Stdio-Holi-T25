# app/curd_operation/user_curd.py

from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from app.database.models import User
from app.schemas.schema import UserCreate, UserResponse
import logging
from app.utils.common_icons import event_icons  # Import event icons for easy access

class UserCRUD:
    """
    A class to encapsulate CRUD operations for the User model.
    """

    def __init__(self):
        # Set up logging
        self.logger = logging.getLogger("uvicorn.error")

    async def create_user(self, db: AsyncSession, user: UserCreate) -> UserResponse:
        """
        Create a new user in the database.

        Args:
            db (AsyncSession): The database session.
            user (UserCreate): The user data to be created.

        Returns:
            UserResponse: The created user data in response format.
        """
        try:
            # Log the incoming user data
            self.logger.info(f"{event_icons['user.create']} Creating user: {user.name}, {user.email}, {user.phone_no}")

            db_user = User(
                name=user.name,
                email=user.email,
                phone_no=user.phone_no,
            )

            # Add the user to the session and commit to the database
            db.add(db_user)
            await db.commit()
            await db.refresh(db_user)

            # Log success
            self.logger.info(f"{event_icons['user.success']} User created with UUID: {db_user.uuid}")
            return UserResponse.from_orm(db_user)

        except SQLAlchemyError as e:
            # Log the error if there's an issue with the DB
            self.logger.error(f"{event_icons['system.error']} SQLAlchemyError while creating user: {str(e)}")
            await db.rollback()
            raise e

    async def get_user_by_uuid(self, db: AsyncSession, uuid: str) -> UserResponse:
        """
        Retrieve a user by their UUID.

        Args:
            db (AsyncSession): The database session.
            uuid (str): The UUID of the user.

        Returns:
            UserResponse or None: The user data if found, otherwise None.
        """
        try:
            query = select(User).filter(User.uuid == uuid)
            result = await db.execute(query)
            user = result.scalars().first()

            if user:
                self.logger.info(f"{event_icons['user.found']} User found with UUID: {uuid}")
                return UserResponse.from_orm(user)

            self.logger.warning(f"{event_icons['user.notfound']} No user found with UUID: {uuid}")
            return None

        except SQLAlchemyError as e:
            self.logger.error(f"{event_icons['system.error']} SQLAlchemyError while retrieving user with UUID {uuid}: {str(e)}")
            raise e

    async def update_user(self, db: AsyncSession, uuid: str, user: UserCreate) -> UserResponse:
        """
        Update user information by their UUID.

        Args:
            db (AsyncSession): The database session.
            uuid (str): The UUID of the user to be updated.
            user (UserCreate): The updated user data.

        Returns:
            UserResponse or None: The updated user data if successful, otherwise None.
        """
        try:
            query = select(User).filter(User.uuid == uuid)
            result = await db.execute(query)
            db_user = result.scalars().first()

            if db_user:
                # Update user fields
                db_user.name = user.name
                db_user.email = user.email
                db_user.phone_no = user.phone_no
                db_user.is_active = user.is_active

                # Commit changes to the database
                await db.commit()
                await db.refresh(db_user)

                self.logger.info(f"{event_icons['user.update']} User updated with UUID: {uuid}")
                return UserResponse.from_orm(db_user)

            self.logger.warning(f"{event_icons['user.notfound']} User with UUID {uuid} not found for update.")
            return None

        except SQLAlchemyError as e:
            self.logger.error(f"{event_icons['system.error']} SQLAlchemyError while updating user with UUID {uuid}: {str(e)}")
            await db.rollback()
            raise e

    async def delete_user(self, db: AsyncSession, uuid: str) -> bool:
        """
        Delete a user by their UUID.

        Args:
            db (AsyncSession): The database session.
            uuid (str): The UUID of the user to be deleted.

        Returns:
            bool: True if the user was deleted successfully, False otherwise.
        """
        try:
            query = select(User).filter(User.uuid == uuid)
            result = await db.execute(query)
            db_user = result.scalars().first()

            if db_user:
                # Delete the user and commit the transaction
                await db.delete(db_user)
                await db.commit()

                self.logger.info(f"{event_icons['user.delete']} User deleted with UUID: {uuid}")
                return True

            self.logger.warning(f"{event_icons['user.notfound']} User with UUID {uuid} not found for deletion.")
            return False

        except SQLAlchemyError as e:
            self.logger.error(f"{event_icons['system.error']} SQLAlchemyError while deleting user with UUID {uuid}: {str(e)}")
            await db.rollback()
            raise e
