from fastapi import FastAPI, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from . import crud, models
from .database import SessionLocal, engine
from datetime import datetime

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request, db: Session = Depends(get_db)):
    customers = crud.get_all_customers(db)
    return templates.TemplateResponse("main_layout.html", {
        "request": request,
        "customers": customers,
        "selected_customer": None,
        "messages": []
    })

@app.get("/customer/{customer_id}", response_class=HTMLResponse)
def read_customer_conversation(request: Request, customer_id: int, db: Session = Depends(get_db)):
    customers = crud.get_all_customers(db)
    selected_customer = crud.get_customer(db, customer_id=customer_id)
    messages = []
    if selected_customer:
        conversation = crud.get_conversation_by_customer_id(db, customer_id=customer_id)
        if conversation:
            messages = crud.get_messages_by_conversation_id(db, conversation_id=conversation.id)

    return templates.TemplateResponse("main_layout.html", {
        "request": request,
        "customers": customers,
        "selected_customer": selected_customer,
        "messages": messages
    })

@app.post("/send_message/{customer_id}")
def send_message(
    customer_id: int,
    message: str = Form(...),
    db: Session = Depends(get_db)
):
    # الخطوة 1: ابحث عن المحادثة
    conversation = crud.get_conversation_by_customer_id(db, customer_id=customer_id)
    
    # الخطوة 2: إذا لم يتم العثور على محادثة، قم بإنشاء واحدة جديدة فوراً
    if not conversation:
        # تأكد من وجود العميل أولاً (إجراء أمان إضافي)
        customer = crud.get_customer(db, customer_id=customer_id)
        if not customer:
            # هذا لا يجب أن يحدث، ولكنه حماية جيدة
            return HTMLResponse("Customer not found", status_code=404)
        
        # قم بإنشاء المحادثة وربطها بالعميل
        conversation = crud.create_conversation(db, customer_id=customer_id)

    # الخطوة 3: الآن بعد أن تأكدنا من وجود محادثة، قم بإنشاء الرسالة
    crud.create_message(
        db=db,
        conversation_id=conversation.id,
        sender="agent",
        content=message,
        timestamp=datetime.utcnow()
    )
    
    # الخطوة 4: أعد توجيه المستخدم ليرى رسالته
    return RedirectResponse(url=f"/customer/{customer_id}", status_code=303)

# Dummy endpoint for WhatsApp webhook verification
@app.get("/webhook")
def verify_webhook(request: Request):
    return "Webhook verified"

# Endpoint to receive messages from WhatsApp
@app.post("/webhook")
async def receive_message(request: Request):
    data = await request.json()
    return {"status": "ok"}
