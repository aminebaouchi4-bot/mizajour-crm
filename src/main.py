from dotenv import load_dotenv
load_dotenv()

import os
from fastapi import (
    FastAPI, Request, Depends, HTTPException, Response, status, WebSocket, WebSocketDisconnect
)
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import logging
import json
from typing import List

from . import crud, models, whatsapp_utils
from .database import SessionLocal, engine

# --- ✨ 1. مدير اتصالات WebSocket ✨ ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

# --- الإعدادات الأخرى (تبقى كما هي) ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
models.Base.metadata.create_all(bind=engine)
app = FastAPI(title="Mizajour.ai", version="5.0.0")
templates = Jinja2Templates(directory="templates")

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

# --- ✨ 2. نقطة نهاية WebSocket ✨ ---
@app.websocket("/ws/{customer_id}")
async def websocket_endpoint(websocket: WebSocket, customer_id: int):
    await manager.connect(websocket)
    logging.info(f"WebSocket connection established for customer {customer_id}")
    try:
        while True:
            # نبقي الاتصال مفتوحاً
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logging.info(f"WebSocket connection closed for customer {customer_id}")

# --- Webhook Endpoints ---
@app.get("/webhook")
def verify_webhook(request: Request):
    # ... (الكود هنا يبقى كما هو)
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return Response(content=challenge, status_code=status.HTTP_200_OK)
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

@app.post("/webhook")
async def receive_whatsapp_message(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    logging.info(f"--- Received new data from WhatsApp ---")
    try:
        if (data.get("entry") and data["entry"][0].get("changes") and
            data["entry"][0]["changes"][0]["value"] and
            data["entry"][0]["changes"][0]["value"].get("messages")):
            message_data = data["entry"][0]["changes"][0]["value"]["messages"][0]
            if message_data.get("type") == "text":
                from_number = message_data["from"]
                message_body = message_data["text"]["body"]
                profile_name = data["entry"][0]["changes"][0]["value"]["contacts"][0]["profile"]["name"]
                customer = crud.get_or_create_customer(db, name=profile_name, phone_number=from_number)
                message = crud.create_message(db, customer_id=customer.id, message_body=message_body, direction="inbound")
                
                # --- ✨ 3. بث الرسالة الجديدة إلى المتصفح ✨ ---
                await manager.broadcast(json.dumps({
                    "type": "new_message",
                    "customerId": customer.id,
                    "html": f"""
                        <div class="flex justify-start">
                            <div class="max-w-xs lg:max-w-md p-3 rounded-lg rounded-br-none bg-slate-700 text-white">
                                <p>{message.content}</p>
                                <p class="text-xs text-slate-400 mt-2 text-left">{message.created_at.strftime('%H:%M')}</p>
                            </div>
                        </div>
                    """
                }))

    except (IndexError, KeyError):
        pass
    return Response(status_code=status.HTTP_200_OK)

# --- Dashboard Endpoints (تبقى كما هي مع تعديل بسيط) ---
@app.post("/customer/{customer_id}/send-message")
async def send_message_from_dashboard(customer_id: int, request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    message_body = data.get("message")
    customer = crud.get_customer_by_id(db, customer_id=customer_id)
    if not customer or not message_body:
        raise HTTPException(status_code=400)
    
    success = whatsapp_utils.send_whatsapp_message(recipient_waid=customer.phone_number, message_text=message_body)
    
    if success:
        message = crud.create_message(db, customer_id=customer.id, message_body=message_body, direction="outbound")
        # --- ✨ 4. بث رسالتك أنت أيضاً ✨ ---
        await manager.broadcast(json.dumps({
            "type": "new_message",
            "customerId": customer.id,
            "html": f"""
                <div class="flex justify-end">
                    <div class="max-w-xs lg:max-w-md p-3 rounded-lg rounded-bl-none bg-sky-600 text-white">
                        <p>{message.content}</p>
                        <p class="text-xs text-sky-200 mt-2 text-left">{message.created_at.strftime('%H:%M')}</p>
                    </div>
                </div>
            """
        }))
        return {"status": "success"}
    else:
        raise HTTPException(status_code=500, detail="Failed to send WhatsApp message")

# ... (باقي نقاط النهاية get / و get /customer/{customer_id} تبقى كما هي) ...
@app.get("/", response_class=HTMLResponse)
def read_root(request: Request, db: Session = Depends(get_db)):
    all_customers = crud.get_all_customers(db)
    return templates.TemplateResponse("main_layout.html", {"request": request, "all_customers": all_customers, "customer": None})

@app.get("/customer/{customer_id}", response_class=HTMLResponse)
def read_customer_conversation(request: Request, customer_id: int, db: Session = Depends(get_db)):
    customer = crud.get_customer_by_id(db, customer_id=customer_id)
    if not customer:
        return RedirectResponse(url="/")
    all_customers = crud.get_all_customers(db)
    return templates.TemplateResponse("main_layout.html", {"request": request, "all_customers": all_customers, "customer": customer})
