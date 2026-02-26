from sqlalchemy.orm import Session
from . import models # <--- لاحظ أننا نحتاج فقط لاستيراد models هنا

# === Customer Functions ===
def get_customer(db: Session, customer_id: int):
    return db.query(models.Customer).filter(models.Customer.id == customer_id).first()

def get_all_customers(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Customer).offset(skip).limit(limit).all()

def create_customer(db: Session, name: str, phone_number: str):
    db_customer = models.Customer(name=name, phone_number=phone_number)
    db.add(db_customer)
    db.commit()
    db.refresh(db_customer)
    return db_customer

# === Conversation Functions ===
def get_conversation(db: Session, conversation_id: int):
    return db.query(models.Conversation).filter(models.Conversation.id == conversation_id).first()

def get_conversation_by_customer_id(db: Session, customer_id: int):
    return db.query(models.Conversation).filter(models.Conversation.customer_id == customer_id).first()

def create_conversation(db: Session, customer_id: int):
    db_conversation = models.Conversation(customer_id=customer_id)
    db.add(db_conversation)
    db.commit()
    db.refresh(db_conversation)
    return db_conversation

# === Message Functions ===
def get_messages_by_conversation_id(db: Session, conversation_id: int):
    return db.query(models.Message).filter(models.Message.conversation_id == conversation_id).order_by(models.Message.timestamp.asc()).all()

def create_message(db: Session, conversation_id: int, sender: str, content: str, timestamp):
    db_message = models.Message(
        conversation_id=conversation_id,
        sender=sender,
        content=content,
        timestamp=timestamp
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message
