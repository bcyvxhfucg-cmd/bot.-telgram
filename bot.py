#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import subprocess
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import json
import re
from flask import Flask
from threading import Thread
import time

# ===========================
# 🔹 توكن البوت (يرجى إبقائه كما هو في القالب)
# ===========================
BOT_TOKEN = "8258339661:AAHSIeEzkDZ5xMEXdnwPfk9xGfchyBwAJ7Q"

# ===========================
# 📦 إنشاء كائنات البوت والسيرفر
# ===========================
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# ===========================
# ⚙️ الثوابت والمسارات
# ===========================
# مسار حفظ الملفات المؤقتة
DOWNLOAD_DIR = "downloads" 
# التأكد من وجود المجلد
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

# ===========================
# 📥 دالة جلب معلومات الوسائط (عامة لجميع المنصات)
# ===========================
def get_media_info(url: str) -> dict:
    """
    الحصول على معلومات الفيديو/الوسائط من أي مصدر يدعمه yt-dlp
    """
    # استخدام yt-dlp -j لـ JSON Output
    command = ['yt-dlp', '-j', url]
    
    try:
        # تنفيذ الأمر والتقاط المخرجات
        result = subprocess.run(command, capture_output=True, text=True, check=True, timeout=15)
        info = json.loads(result.stdout)
        return info
    except subprocess.CalledProcessError as e:
        print(f"❌ خطأ في yt-dlp: {e.stderr}")
        return {"error": e.stderr}
    except json.JSONDecodeError:
        print("❌ فشل تحليل JSON من yt-dlp")
        return {"error": "Failed to decode media info."}
    except subprocess.TimeoutExpired:
        print("❌ انتهت مهلة جلب المعلومات.")
        return {"error": "Timeout while fetching info."}
    except Exception as e:
        print(f"❌ خطأ غير متوقع في جلب المعلومات: {e}")
        return {"error": str(e)}

# ===========================
# 🚀 دالة تحميل الوسائط (عامة لجميع المنصات)
# ===========================
def download_media(url: str, format_type: str, file_name: str) -> str:
    """
    تحميل الوسائط (فيديو أو صوت) وتحديد مسار الإخراج.
    """
    output_path = os.path.join(DOWNLOAD_DIR, f"{file_name}.%(ext)s")
    
    if format_type == "video":
        # أفضل فيديو بجودة عالية متوفرة (يفضل mp4)
        fmt = "bestvideo[ext=mp4]+bestaudio/best[ext=mp4]/best"
    elif format_type == "audio":
        # أفضل صوت فقط وتحويله إلى mp3
        fmt = "bestaudio[ext=m4a]/bestaudio"
        command = [
            'yt-dlp', 
            '-f', fmt, 
            '-x', # استخراج الصوت
            '--audio-format', 'mp3', # تحويل للصيغة المطلوبة
            '--add-metadata',
            '--restrict-filenames', 
            '-o', output_path, 
            '--no-warnings', 
            url
        ]
        
        # لتنزيل الفيديو (مع أو بدون صوت حسب الطلب)
    else: # video or default
        command = [
            'yt-dlp', 
            '-f', fmt, 
            '--merge-output-format', 'mp4',
            '--add-metadata',
            '--restrict-filenames', 
            '-o', output_path, 
            '--no-warnings', 
            url
        ]
        
    try:
        # تنفيذ الأمر
        subprocess.run(command, check=True, timeout=600) # مهلة 10 دقائق
        
        # البحث عن الملف الذي تم تنزيله (yt-dlp يضيف الامتداد)
        for f in os.listdir(DOWNLOAD_DIR):
            if f.startswith(file_name):
                return os.path.join(DOWNLOAD_DIR, f)
        
        return "" # فشل في إيجاد الملف بعد التنزيل
        
    except subprocess.CalledProcessError as e:
        print(f"❌ خطأ في عملية التحميل: {e.stderr}")
        return ""
    except subprocess.TimeoutExpired:
        print("❌ انتهت مهلة التحميل.")
        return ""
    except Exception as e:
        print(f"❌ خطأ غير متوقع أثناء التحميل: {e}")
        return ""

# ===========================
# ⚡ أوامر البوت
# ===========================

@bot.message_handler(commands=['start'])
def start_handler(msg):
    # رسالة ترحيبية فخمة
    welcome_message = (
        "💎 **أهلاً بك في بوت التحميل السريع الشامل!** 🚀\n"
        "أنا هنا لتحميل المحتوى من **يوتيوب، إنستغرام، تيك توك، وفيسبوك** وأغلب منصات التواصل الاجتماعي الأخرى.\n\n"
        "✨ **كيف يعمل البوت؟**\n"
        "1. **أرسل رابط** أي فيديو أو وسائط مدعومة.\n"
        "2. سأجلب المعلومات وأعرض لك **خيارات التحميل (فيديو 📹 أو صوت 🎵)**.\n"
        "3. اضغط على خيارك المفضل، وستحصل على الملف بأعلى جودة ممكنة دون علامات مائية.\n\n"
        "✅ **الآن، أرسل رابطك الأول لتبدأ المتعة!**"
    )
    bot.reply_to(msg, welcome_message, parse_mode="Markdown")

@bot.message_handler(func=lambda msg: True)
def handle_message(msg):
    url = msg.text.strip()
    
    # تحقق بسيط من أن النص هو رابط صالح (قد يحتوي على بروتوكول http/https)
    if not re.match(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+', url):
        bot.reply_to(msg, "⚠️ **تنبيه:** يرجى إرسال **رابط صالح** لوسائط من يوتيوب، إنستغرام، تيك توك، أو غيرها. 🔗")
        return

    processing_msg = bot.reply_to(msg, "⏳ **جاري تحليل الرابط... يرجى الانتظار للحظات.** 🕵️")
    
    info = get_media_info(url)
    
    if "error" in info or not info:
        error_msg = info.get("error", "حدث خطأ غير معروف في جلب معلومات الوسائط.")
        bot.edit_message_text(f"❌ **فشل جلب معلومات الوسائط:**\nقد يكون الرابط غير مدعوم، خاص، أو يحتوي على خطأ. ({error_msg})", 
                              msg.chat.id, processing_msg.message_id, parse_mode="Markdown")
        return
    
    # الحصول على معلومات أساسية
    title = info.get('title', 'لا يتوفر عنوان')
    extractor = info.get('extractor', 'مصدر غير محدد').replace(":", " ").capitalize()
    duration = info.get('duration')
    duration_str = f"{int(duration // 60)}:{int(duration % 60):02d}" if duration else "غير متوفر"

    # إعداد رسالة المعلومات الفخمة
    caption = (
        f"🌟 **تم تحليل الرابط بنجاح!** 🌟\n\n"
        f"🔗 **المنصة:** {extractor}\n"
        f"🏷️ **العنوان:** {title}\n"
        f"⏱️ **المدة:** {duration_str}\n"
        f"👤 **الناشر:** {info.get('uploader', 'غير متوفر')}\n\n"
        f"👇 **اختر جودة ونوع التحميل:**"
    )

    # إنشاء أزرار التحميل
    markup = InlineKeyboardMarkup()
    
    # استخدام العنوان كجزء من اسم الملف لجعله فريدًا
    file_id_segment = str(hash(url) % 100000) 
    
    # زر تحميل الفيديو
    video_btn_text = "📹 تحميل فيديو (أعلى جودة)"
    markup.add(
        InlineKeyboardButton(video_btn_text, callback_data=f"video|{file_id_segment}|{url}")
    )
    
    # زر تحميل الصوت فقط (إذا كانت المدة معقولة)
    if duration is None or duration < 1000: # تجنب محاولة تنزيل صوت لساعات من البث المباشر
        audio_btn_text = "🎵 تحميل صوت (MP3)"
        markup.add(
            InlineKeyboardButton(audio_btn_text, callback_data=f"audio|{file_id_segment}|{url}")
        )

    # إرسال الرسالة الجديدة وإزالة رسالة المعالجة القديمة
    bot.delete_message(msg.chat.id, processing_msg.message_id)
    bot.send_message(msg.chat.id, caption, reply_markup=markup, parse_mode="Markdown")

# ===========================
# 🎯 التعامل مع الضغط على الأزرار
# ===========================

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    # تنسيق call.data: action|file_id_segment|url
    try:
        action, file_id_segment, url = call.data.split("|", 2)
    except ValueError:
        bot.answer_callback_query(call.id, "❌ خطأ في بيانات الزر.", show_alert=True)
        return

    # إزالة الأزرار وعرض حالة التحميل
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    
    # إرسال رسالة "جاري التحميل" الجديدة 
    download_msg = bot.send_message(call.message.chat.id, "⏳ **بدء عملية التحميل...** قد تستغرق العملية بعض الوقت حسب حجم الملف. ⚙️", parse_mode="Markdown")

    file_name = f"download_{call.message.chat.id}_{file_id_segment}_{action}_{int(time.time())}"
    
    # تنفيذ عملية التحميل
    file_path = download_media(url, format_type=action, file_name=file_name)

    # حذف رسالة "جاري التحميل"
    try:
        bot.delete_message(call.message.chat.id, download_msg.message_id)
    except Exception:
        pass # قد يكون تم حذفها بالفعل أو حدث خطأ في الحذف

    if not file_path:
        bot.send_message(call.message.chat.id, "❌ **فشل التحميل!** \nتعذر تحميل الوسائط. يرجى التأكد من أن الرابط عام وغير محمي.", parse_mode="Markdown")
        return

    # إرسال الملف
    try:
        with open(file_path, "rb") as media_file:
            caption_text = f"✅ **تم التحميل بنجاح!** ✨\n\nنوع الملف: {'فيديو 📹' if action == 'video' else 'صوت 🎵'}"
            
            if action == "video":
                # إرسال فيديو
                bot.send_video(call.message.chat.id, media_file, caption=caption_text, parse_mode="Markdown", supports_streaming=True)
            elif action == "audio":
                # إرسال صوت
                bot.send_audio(call.message.chat.id, media_file, caption=caption_text, parse_mode="Markdown")
            else:
                 # إرسال مستند في حال عدم التحديد
                 bot.send_document(call.message.chat.id, media_file, caption=caption_text, parse_mode="Markdown")

    except Exception as e:
        print(f"❌ خطأ في إرسال الملف: {e}")
        bot.send_message(call.message.chat.id, f"❌ **فشل إرسال الملف:** \nقد يكون حجم الملف كبيراً جداً ({e}).", parse_mode="Markdown")
    
    finally:
        # تنظيف الملفات المؤقتة
        if os.path.exists(file_path):
            os.remove(file_path)
            
        # إشعار للمستخدم بأن العملية انتهت
        bot.answer_callback_query(call.id, text="تمت العملية بنجاح!")


# ===========================
# 🟢 تشغيل البوت باستخدام Thread
# ===========================

def run_bot():
    print("🤖 Super Downloader Bot is running...")
    # إزالة الأخطاء التي تظهر عند إعادة التشغيل
    try:
        bot.delete_webhook()
    except Exception as e:
        print(f"Failed to delete webhook: {e}")
    
    bot.infinity_polling(skip_pending=True)

# ===========================
# 🌐 إضافة endpoint لاستقبال Ping
# ===========================

@app.route('/')
def home():
    return "✅ السيرفر يعمل! Super Downloader Bot جاهز للـ Ping."

# ===========================
# 🏁 تشغيل Flask + البوت
# ===========================

if __name__ == "__main__":
    from waitress import serve
    import threading

    # تشغيل البوت في Thread منفصل
    t = threading.Thread(target=run_bot)
    t.start()

    # تشغيل Flask عبر Waitress على جميع العناوين
    port = int(os.environ.get("PORT", 5000))
    print(f"🌐 السيرفر يعمل على المنفذ {port}")
    serve(app, host="0.0.0.0", port=port)
