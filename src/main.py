# src/main.py - الإصدار الذهبي (مستقر)

from dotenv import load_dotenv
load_dotenv()

import os
import logging
from fastapi import FastAPI, Request, Depends, HTTPException, Response, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from . import crud, models, whatsapp_utils
from .database import SessionLocal, engine

# --- الإعداد الأولي ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
if not VERIFY_TOKEN:
    raise ValueError("لم يتم العثور على متغير VERIFY_TOKEN.")

models.Base.metadata.create_all(bind=engine)
app = FastAPI(title="Mizajour.ai", version="3.0-stable")
templates = Jinja2Templates(directory="templates")

# --- الاعتماديات ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- نقاط نهاية الـ Webhook ---
@app.get("/webhook")
def verify_webhook(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        logging.info(">>> نجاح التحقق من الـ Webhook!")
        return Response(content=challenge, status_code=status.HTTP_200_OK)
    else:
        logging.error("!!! فشل التحقق من الـ Webhook.")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Verify token mismatch")

@app.post("/webhook")
async def receive_whatsapp_message(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    logging.info(f"--- Received new data from WhatsApp ---\n{data}")
    
    try:
        # استخراج المعلومات الأساسية
        change = data['entry'][0]['changes'][0]
        if change['field'] == 'messages':
            message_data = change['value']['messages'][0]
            profile_name = change['value']['contacts'][0]['profile']['name']
            from_number = message_data['from']
            message_body = message_data['text']['body']

            logging.info(f"Processing message from {profile_name} ({from_number})")

            # الحصول على العميل أو إنشائه
            customer = crud.get_or_create_customer(db, name=profile_name, phone_number=from_number)
            
            # حفظ الرسالة
            crud.create_message(db, customer_id=customer.id, content=message_body, sender_type='customer')
            logging.info(f"Successfully saved message for customer ID: {customer.id}")

    except (KeyError, IndexError) as e:
        logging.warning(f"Could not parse message data, skipping. Error: {e}")

    return Response(status_code=status.HTTP_200_OK)

# --- نقاط نهاية لوحة التحكم ---
@app.get("/", response_class=HTMLResponse)
def read_root(request: Request, db: Session = Depends(get_db)):
    all_customers = crud.get_all_customers(db)
    return templates.TemplateResponse("main_layout.html", {
        "request": request,
        "customers": all_customers,
        "selected_customer": None # لا يوجد عميل محدد في البداية
    })

@app.get("/customer/{customer_id}", response_class=HTMLResponse)
def read_customer_conversation(request: Request, customer_id: int, db: Session = Depends(get_db)):
    all_customers = crud.get_all_customers(db)
    selected_customer = crud.get_customer_by_id(db, customer_id=customer_id)
    if not selected_customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    return templates.TemplateResponse("main_layout.html", {
        "request": request,
        "customers": all_customers,
        "selected_customer": selected_customer
    })

# --- نقطة نهاية إرسال الرسائل (معطلة مؤقتاً) ---
@app.post("/customer/{customer_id}/send-message")
async def send_message_from_dashboard(customer_id: int, request: Request, db: Session = Depends(get_db)):
    # هذا الجزء معطل عمداً لتجنب المشاكل. سنعود إليه لاحقاً.
    logging.warning("Send message functionality is currently disabled.")
    return JSONResponse(
        content={"success": False, "message": "Send functionality is disabled."},
        status_code=501, # Not Implemented
    )
