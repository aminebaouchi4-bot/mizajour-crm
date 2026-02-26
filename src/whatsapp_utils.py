import requests
import json
import logging
from dotenv import load_dotenv
import os

# تحميل المتغيرات من ملف .env
load_dotenv()

# --- قراءة المتغيرات من البيئة ---
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
VERSION = "v18.0"

# التحقق من وجود المتغيرات
if not all([ACCESS_TOKEN, PHONE_NUMBER_ID]):
    raise ValueError("لم يتم العثور على متغيرات واتساب (ACCESS_TOKEN, PHONE_NUMBER_ID). تأكد من وجودها في ملف .env")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def send_whatsapp_message(recipient_waid: str, message_text: str) -> bool:
    url = f"https://graph.facebook.com/{VERSION}/{PHONE_NUMBER_ID}/messages"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"}
    payload = {"messaging_product": "whatsapp", "to": recipient_waid, "type": "text", "text": {"preview_url": False, "body": message_text}}
    
    logging.info(f"إعداد لإرسال رسالة إلى {recipient_waid}..." )
    logging.info(f"URL الهدف: {url}")
    logging.info(f"Headers: {{'Authorization': 'Bearer [TOKEN REDACTED]', 'Content-Type': 'application/json'}}")
    logging.info(f"البيانات المرسلة (Payload): {json.dumps(payload, indent=2, ensure_ascii=False)}")

    try:
        # --- التعديل الرئيسي: زيادة مهلة الاتصال إلى 60 ثانية ---
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        
        response.raise_for_status()
        response_data = response.json()
        logging.info(f"تم استلام رد من فيسبوك: {response_data}")
        
        if "messages" in response_data and response_data["messages"][0]["id"]:
            logging.info(">>> نجاح! تم تأكيد استلام الطلب من قبل خوادم واتساب.")
            return True
        else:
            logging.error(f"فشل الإرسال: الرد من فيسبوك لا يحتوي على معرف الرسالة المتوقع.")
            return False
            
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"!!! خطأ HTTP فادح حدث: {http_err}" )
        logging.error(f"محتوى الرد (سبب الخطأ): {http_err.response.text}" )
        return False
    except requests.exceptions.RequestException as req_err:
        # هذا هو الخطأ الذي يظهر لك (Timeout)، لذلك أضفت طباعة أوضح له
        logging.error(f"!!! خطأ في الاتصال بالشبكة حدث: {req_err}")
        logging.error("هذا يعني أن الكود لم يتمكن من الوصول إلى خوادم فيسبوك. تحقق من اتصال الإنترنت، جدار الحماية، أو برامج مكافحة الفيروسات.")
        return False
    except Exception as err:
        logging.error(f"!!! خطأ غير متوقع حدث: {err}")
        return False

# --- قسم الاختبار ---
if __name__ == "__main__":
    RECIPIENT_NUMBER = "213676219720" # رقمك الشخصي للاختبار
    
    print("\n" + "="*50)
    print("---   بدء اختبار إرسال رسالة واتساب مستقل   ---")
    print("="*50 + "\n")
    
    success = send_whatsapp_message(
        recipient_waid=RECIPIENT_NUMBER, 
        message_text="مرحباً من Mizajour.ai! 👋\nهذا اختبار ناجح باستخدام متغيرات .env."
    )
    
    print("\n" + "="*50)
    if success:
        print("--- ✅ انتهى الاختبار بنجاح. ---")
    else:
        print("--- ❌ انتهى الاختبار بفشل. ---")
    print("="*50 + "\n")
