    #  app/database/models.py

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Enum,Float
from sqlalchemy.orm import relationship
import uuid
import datetime
from datetime import datetime
from app.database.base import Base  # ✅ Use a single Base from base.py

class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "public"}

    uuid = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(50), nullable=False)
    email = Column(String(100), nullable=False)
    phone_no = Column(String(16), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    orders = relationship("Order", back_populates="user", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="user", cascade="all, delete-orphan")
    qr_codes = relationship("QRCode", back_populates="user", cascade="all, delete-orphan")
    sms = relationship("SMS", back_populates="user", cascade="all, delete-orphan")
    emails = relationship("Email", back_populates="user", cascade="all, delete-orphan")

    def as_dict(self):
        """Convert SQLAlchemy object to dict with serialized datetime."""
        return {
            "uuid": self.uuid,
            "name": self.name,
            "email": self.email,
            "phone_no": self.phone_no,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),  # Convert to string
            "updated_at": self.updated_at.isoformat()   # Convert to string
        }
    
    def __repr__(self):
        return f"<User(uuid={self.uuid}, name='{self.name}', email='{self.email}', phone_no='{self.phone_no}')>"

class Order(Base):
    __tablename__ = "orders"

    uuid = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_uuid = Column(String(36), ForeignKey('public.users.uuid', ondelete="CASCADE"), nullable=False)
    razorpay_order_id = Column(String(50), nullable=False, unique=True)  # Razorpay order tracking
    total_amount = Column(Float, nullable=False)
    order_status = Column(Enum('created', 'paid', 'cancelled', name='order_status'), default='created')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="orders")
    payments = relationship("Payment", back_populates="order", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Order(uuid={self.uuid}, razorpay_order_id={self.razorpay_order_id}, total_amount={self.total_amount}, order_status={self.order_status})>"

class Payment(Base):
    __tablename__ = "payments"

    uuid = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_uuid = Column(String(36), ForeignKey('public.users.uuid', ondelete="CASCADE"), nullable=False)
    ticket_description = Column(String(500), nullable=False)
    ticket_type = Column(String(50), nullable=False)
    ticket_price = Column(Integer, nullable=False)
    ticket_qty = Column(Integer, nullable=False)
    payment_method = Column(String(50), nullable=False)
    order_uuid = Column(String(36), ForeignKey('orders.uuid', ondelete="CASCADE"), nullable=False)  # Link to Order
    razorpay_payment_id = Column(String(50), nullable=False, unique=True)  # Razorpay payment tracking
    transaction_id = Column(String(50), nullable=False)
    discount = Column(Float, nullable=False, default=0.0)
    transaction_fee = Column(Float, nullable=False)
    invoice_amount = Column(Float, nullable=False, default=0.0)
    gst = Column(Float, nullable=False, default=0.0)
    total_tax = Column(Float, nullable=False, default=0.0)
    total_amount = Column(Float, nullable=False, default=0.0)
    transaction_status = Column(Enum('successful', 'failed', 'processing', 'cancelled', 'due', name='payment_status'), nullable=False)
    order_date = Column(DateTime, default=datetime.utcnow)
    issued_date = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="payments")
    order = relationship("Order", back_populates="payments", cascade="all, delete-orphan")
    qr_codes = relationship("QRCode", back_populates="payment", cascade="all, delete-orphan")
    sms = relationship("SMS", back_populates="payment", cascade="all, delete-orphan")
    emails = relationship("Email", back_populates="payment", cascade="all, delete-orphan")

    def to_dict(self):
        return (f"<Payment(uuid={self.uuid}, user_uuid={self.user_uuid}, ticket_description='{self.ticket_description}', "
                f"ticket_type='{self.ticket_type}', ticket_price={self.ticket_price}, ticket_qty={self.ticket_qty}, "
                f"payment_method='{self.payment_method}',order_uuid={self.order_uuid}, razorpay_payment_id={self.razorpay_payment_id}, transaction_id='{self.transaction_id}', transaction_fee={self.transaction_fee}, "
                f"invoice_amount={self.invoice_amount}, discount={self.discount}, gst={self.gst}, i_gst={self.i_gst}, "
                f"s_gst={self.s_gst}, c_gst={self.c_gst}, total_tax={self.total_tax}, total_amount={self.total_amount}, "
                f"transaction_status='{self.transaction_status}', issued_date='{self.issued_date}', updated_at='{self.updated_at}')>"
            )
    
class QRCode(Base):
    __tablename__ = "qr_codes"

    uuid = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_uuid = Column(String(36), ForeignKey('public.users.uuid', ondelete="CASCADE"), nullable=False)
    payment_uuid = Column(String(36), ForeignKey('payments.uuid', ondelete="CASCADE"), nullable=False)
    qr_code = Column(String(255), nullable=False)
    qr_unique_id = Column(String(50), nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="qr_codes")
    payment = relationship("Payment", back_populates="qr_codes")
    sms = relationship("SMS", back_populates="qr_code", cascade="all, delete-orphan")
    emails = relationship("Email", back_populates="qr_code", cascade="all, delete-orphan")

    def to_dict(self):
        return (f"<QRCode(uuid={self.uuid}, user_uuid={self.user_uuid}, payment_uuid={self.payment_uuid}, "
                f"qr_code='{self.qr_code}', qr_unique_id='{self.qr_unique_id}', created_at='{self.created_at}', "
                f"updated_at='{self.updated_at}')>")

class SMS(Base):
    __tablename__ = "sms"

    uuid = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_uuid = Column(String(36), ForeignKey('public.users.uuid', ondelete="CASCADE"), nullable=False)
    payment_uuid = Column(String(36), ForeignKey('payments.uuid', ondelete="CASCADE"), nullable=True)
    qr_code_uuid = Column(String(36), ForeignKey('qr_codes.uuid', ondelete="CASCADE"), nullable=True)
    phone_number = Column(String(16), nullable=False)
    message = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="sms")
    payment = relationship("Payment", back_populates="sms")
    qr_code = relationship("QRCode", back_populates="sms")
    emails = relationship("Email", back_populates="sms", cascade="all, delete-orphan")

    def to_dict(self):
        return (f"<SMS(uuid={self.uuid}, user_uuid={self.user_uuid}, payment_uuid={self.payment_uuid}, "
                f"qr_code_uuid={self.qr_code_uuid}, mobile_no='{self.mobile_no}', message='{self.message}', "
                f"message_send_confirmation='{self.message_send_confirmation}', created_at='{self.created_at}', "
                f"updated_at='{self.updated_at}')>")

class Email(Base):
    __tablename__ = "emails"

    uuid = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_uuid = Column(String(36), ForeignKey('public.users.uuid', ondelete="CASCADE"), nullable=False)
    payment_uuid = Column(String(36), ForeignKey('payments.uuid', ondelete="CASCADE"), nullable=True)
    qr_code_uuid = Column(String(36), ForeignKey('qr_codes.uuid', ondelete="CASCADE"), nullable=True)
    sms_uuid = Column(String(36), ForeignKey('sms.uuid', ondelete="CASCADE"), nullable=True)
    email = Column(String(100), nullable=False)
    message = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="emails")
    payment = relationship("Payment", back_populates="emails")
    qr_code = relationship("QRCode", back_populates="emails")
    sms = relationship("SMS", back_populates="emails")

    def to_dict(self):
        return f"<Email(id={self.uuid}, user_id={self.user_uuid}, email='{self.email}', message='{self.message}', created_at='{self.created_at}', updated_at='{self.updated_at}')>"