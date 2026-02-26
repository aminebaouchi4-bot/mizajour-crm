from sqlalchemy.orm import Session
from . import models

def get_customer_by_phone(db: Session, phone_number: str):
    return db.query(models.Customer).filter(models.Customer.phone_number == phone_number).first()

def get_customer_by_id(db: Session, customer_id: int):
    return db.query(models.Customer).filter(models.Customer.id == customer_id).first()

def get_all_customers(db: Session):
    return db.query(models.Customer).order_by(models.Customer.created_at.desc()).all()

def get_or_create_customer(db: Session, name: str, phone_number: str) -> models.Customer:
    customer = get_customer_by_phone(db, phone_number=phone_number)
    if not customer:
        customer = models.Customer(name=name, phone_number=phone_number)
        db.add(customer)
        db.commit()
        db.refresh(customer)
    elif customer.name != name:
        customer.name = name
        db.commit()
        db.refresh(customer)
    return customer

# --- ✨✨ التغييرات الأساسية هنا ✨✨ ---
def create_message(db: Session, customer_id: int, message_body: str, direction: str):
    # نقوم بتعيين القيم للأسماء الصحيحة للأعمدة
    db_message = models.Message(
        customer_id=customer_id,
        content=message_body,      # body -> content
        sender_type=direction      # direction -> sender_type
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message
