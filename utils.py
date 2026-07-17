import secrets
import re
from urllib.parse import urlparse

def generate_session_id():
    """إنشاء معرف جلسة عشوائي"""
    return secrets.token_urlsafe(12)

def is_valid_url(url):
    """التحقق من صحة الرابط"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def extract_youtube_id(url):
    """استخراج معرف الفيديو من رابط يوتيوب"""
    patterns = [
        r'youtube\.com/watch\?v=([^&]+)',
        r'youtu\.be/([^?]+)',
        r'youtube\.com/embed/([^?]+)'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def create_short_link(session_id, original_url):
    """إنشاء رابط مختصر يحاكي الرابط الأصلي"""
    parsed = urlparse(original_url)
    domain = parsed.netloc
    
    # استخدم أول 8 حروف من session_id
    short_id = session_id[:8]
    
    # بناء الرابط المختصر بنفس شكل الرابط الأصلي
    if 'youtube.com' in domain or 'youtu.be' in domain:
        # رابط يوتيوب
        video_id = extract_youtube_id(original_url)
        if video_id:
            return f"https://youtu.be/{short_id}"
        else:
            return f"https://youtu.be/{short_id}"
    
    # روابط أخرى
    return f"https://{domain}/{short_id}"