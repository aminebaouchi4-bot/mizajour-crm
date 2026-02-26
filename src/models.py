from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .database import Base

class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=True)
    phone_number = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    lead_status = Column(String, default="New")

    messages = relationship("Message", back_populates="customer")

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    
    # --- ✨✨ التغييرات الأساسية هنا ✨✨ ---
    content = Column(String, nullable=False) # اسم العمود هو content
    sender_type = Column(String, nullable=False) # اسم العمود هو sender_type
    created_at = Column(DateTime(timezone=True), server_default=func.now()) # اسم العمود هو created_at

    customer = relationship("Customer", back_populates="messages")
