from pydantic import BaseModel
from datetime import datetime
from typing import List

# هذا يحدد شكل البيانات عند قراءتها من قاعدة البيانات
class Message(BaseModel):
    id: int
    content: str
    sender_type: str
    created_at: datetime
    class Config:
        from_attributes = True

class Conversation(BaseModel):
    id: int
    messages: List[Message] = []
    class Config:
        from_attributes = True

class Customer(BaseModel):
    id: int
    phone_number: str
    lead_status: str
    created_at: datetime
    conversations: List[Conversation] = []
    class Config:
        from_attributes = True
