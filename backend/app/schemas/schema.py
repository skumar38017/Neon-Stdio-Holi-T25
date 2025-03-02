#  app/schemas/schema.py

from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime
from pydantic import BaseModel
from app.utils.validator import validate_phone  # Import custom phone number validator

# User Schema
class UserBase(BaseModel):
    name: str = Field(..., max_length=50)
    email: EmailStr
    phone_no: str = Field(..., max_length=16, min_length=10)  # Adjusted for international phone support

    @field_validator("phone_no")
    @classmethod
    def validate_phone_no(cls, value):
        return validate_phone(value)

class UserCreate(UserBase):
    pass

class UserResponse(UserBase):
    uuid: str
    name: str
    email: str
    phone_no: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 
        json_encoders = {
            datetime: lambda v: v.isoformat()  # Automatically convert datetime
        } 

# VerifyBase Schema
class VerifyBase(BaseModel):
    otp: str

# VerifyOTPResponse Schema
class VerifyOTPResponse(BaseModel):
    message: str
    redis_key: str  # The Redis key generated for the user
    task_id: str
    success: bool
    session_id: str

# TicketChoice Schema
class TicketChoice(BaseModel):
    user_uuid: str
    ticket_description: str = Field(..., max_length=500)
    ticket_type: str = Field(..., max_length=50)
    ticket_price: int
    ticket_qty: int
    payment_method: str = Field(..., max_length=50)

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()  # Automatically convert datetime
        }   

# Payment Schema
class PaymentData(BaseModel):
    user_uuid: str
    amount: int
    payment_method: str = Field(..., example="credit_card")

    @field_validator('amount')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError("Amount must be greater than 0")
        return v

# Order Schema
class OrderBase(BaseModel):
    razorpay_order_id: str = Field(..., max_length=50)
    ticket_type: str = Field(..., max_length=50)
    ticket_price: int
    ticket_qty: int
    discount: float = 0  # Corrected spelling from 'disscount' to 'discount'
    total_amount: float
    order_status: str = Field(..., pattern="^(created|paid|cancelled)$")

class OrderCreate(OrderBase):
    user_uuid: str

class OrderResponse(OrderBase):
    uuid: str
    user_uuid: str
    razorpay_order_id: str = Field(..., max_length=50)
    ticket_type: str = Field(..., max_length=50)
    ticket_price: int
    ticket_qty: int
    discount: float = 0  # Corrected spelling from 'disscount' to 'discount'
    total_amount: float
    order_status: str = Field(..., pattern="^(created|paid|cancelled)$")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()  # Automatically convert datetime
        } 

class PaymentBase(BaseModel):
    ticket_description: str = Field(..., max_length=500)
    ticket_type: str = Field(..., max_length=50)
    ticket_price: int
    ticket_qty: int
    payment_method: str = Field(..., max_length=50, example="credit_card")
    razorpay_payment_id: str = Field(..., max_length=50)
    transaction_id: str = Field(..., max_length=50)
    discount: float = 0  # Corrected spelling from 'disscount' to 'discount'
    transaction_fee: float
    invoice_amount: float = 0
    gst: float = 0
    i_gst: float = 0
    s_gst: float = 0
    c_gst: float = 0
    total_tax: float = 0
    total_amount: float = 0
    transaction_status: str = Field(..., pattern="^(successful|failed|processing|cancelled|due)$")  # Fixed regex pattern

class PaymentCreate(PaymentBase):
    user_uuid: str
    order_uuid: str

class PaymentResponse(PaymentBase):
    uuid: str
    user_id: str
    ticket_description: str
    ticket_type: str
    ticket_price: str
    ticket_qty: str
    payment_method: str
    razorpay_order_id: str
    razorpay_payment_id: str
    transaction_id: str
    discount: float  # Corrected typo here
    transaction_fee: float
    invoice_amount: float
    gst: float
    i_gst: float
    s_gst: float    
    c_gst: float
    total_tax: float
    total_amount: float
    transaction_status: str
    issued_date: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()  # Automatically convert datetime
        } 

# QR Code Schema
class QRCodeBase(BaseModel):
    qr_code: str = Field(..., max_length=50)
    qr_unique_id: str = Field(..., max_length=50)


class QRCodeCreate(QRCodeBase):
    user_id: str
    payment_uuid: str


class QRCodeResponse(QRCodeBase):
    uuid: str
    user_id: str
    payment_uuid: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()  # Automatically convert datetime
        } 

# SMS Schema
class SMSBase(BaseModel):
    mobile_no: str = Field(..., max_length=10, min_length=10)
    message: str = Field(..., max_length=500)
    message_send_confirmation: str = Field(..., pattern="^(successfully|failed)$")


class SMSCreate(SMSBase):
    user_id: str
    payment_uuid: str
    qr_code_uuid: str


class SMSResponse(SMSBase):
    uuid: str
    user_id: str
    payment_uuid: str
    qr_code_uuid: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()  # Automatically convert datetime
        } 

# Email Schema
class EmailBase(BaseModel):
    email: EmailStr
    message: str = Field(..., max_length=50)


class EmailCreate(EmailBase):
    user_id: str


class EmailResponse(EmailBase):
    uuid: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()  # Automatically convert datetime
        } 
