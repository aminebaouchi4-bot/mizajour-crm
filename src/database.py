from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

# تحميل المتغيرات من ملف .env الموجود في جذر المشروع
load_dotenv()

# قراءة رابط قاعدة البيانات من متغيرات البيئة
DATABASE_URL = os.getenv("DATABASE_URL")

# التأكد من أن الرابط موجود قبل المتابعة
if not DATABASE_URL:
    raise ValueError("لم يتم العثور على متغير DATABASE_URL. تأكد من وجوده في ملف .env")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
