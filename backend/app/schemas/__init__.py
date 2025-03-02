#  app/schemas/__init__.py

from app.schemas.schema import UserBase, UserCreate, UserResponse, VerifyOTPResponse, VerifyBase
from app.schemas.schema import TicketChoice
from app.schemas.schema import PaymentBase, PaymentCreate, PaymentResponse
from app.schemas.schema import QRCodeBase, QRCodeCreate, QRCodeResponse
from app.schemas.schema import SMSBase, SMSCreate, SMSResponse
from app.schemas.schema import EmailBase, EmailCreate, EmailResponse

# Optionally, you can also export interfaces if needed
from app.schemas.interfaces import (
    UserInterface,
    PaymentInterface,
    QRCodeInterface,
    SMSInterface,
    VerifyOTPResponseInterface,
    EmailInterface,
    UserResponseInterface,
    PaymentResponseInterface,
    QRCodeResponseInterface,
    SMSResponseInterface,
    EmailResponseInterface,
)