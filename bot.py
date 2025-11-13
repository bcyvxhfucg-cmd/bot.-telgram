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
# 🔹 توكن البوت
# ===========================
BOT_TOKEN = os.getenv("BOT_TOKEN", "8258339661:AAHSIeEzkDZ5xMEXdnwPfk9xGfchyBwAJ7Q")

# ===========================
# 📦 إنشاء كائنات البوت والسيرفر
# ===========================
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# ===========================
# ⚙️ إعدادات المسارات
# ===========================
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# ===========================
# 📥 جلب معلومات الوسائط باستخدام yt-dlp
# ===========================
def get_media_info(url: str) -> dict:
    try:
        result = subprocess.run(['yt-dlp', '-j', url], capture_output=True, text=True, check=True, timeout=20)
        return json.loads(result.stdout)
    except subprocess.TimeoutExpired:
        return {"error": "⏱️ انتهت المهلة أثناء تحليل الرابط."}
    except subprocess.CalledProcessError as e:
        return {"error": e.stderr or "❌ فشل تنفيذ yt-dlp"}
    except Exception as e:
        return {"error": str(e)}

# ===========================
# 🚀 تحميل الوسائط (فيديو أو صوت)
# ===========================
def download_media(url: str, format_type: str, file_name: str) -> str:
    output_path = os.path.join(DOWNLOAD_DIR, f"{file_name}.%(ext)s")

    if format_type == "audio":
        fmt = "bestaudio[ext=m4a]/bestaudio"
        cmd = ['yt-dlp', '-f', fmt, '-x', '--audio-format', 'mp3', '-o', output_path, url]
    else:
        fmt = "bestvideo[ext=mp4]+bestaudio/best"
        cmd = ['yt-dlp', '-f', fmt, '--merge-output-format', 'mp4', '-o', output_path, url]

    try:
        subprocess.run(cmd, check=True, timeout=600)
        for f in os.listdir(DOWNLOAD_DIR):
            if f.startswith(file_name):
                return os.path.join(DOWNLOAD_DIR, f)
    except subprocess.TimeoutExpired:
        print("⏰ انتهت مهلة التحميل.")
    except Exception as e:
        print(f"❌ خطأ أثناء التحميل: {e}")
    return ""

# ===========================
# ⚡ أوامر البوت
# ===========================
@bot.message_handler(commands=['start'])
def start_handler(msg):
    text = (
        "👋 **مرحبًا بك في بوت التحميل الفائق!**\n"
        "📥 أرسل أي رابط من Instagram أو YouTube أو TikTok أو Facebook.\n"
        "وسأعطيك خيارات تحميل الفيديو أو الصوت مباشرة. 🚀"
    )
    bot.reply_to(msg, text, parse_mode="Markdown")

@bot.message_handler(func=lambda m: True)
def link_handler(msg):
    url = msg.text.strip()
    if not re.match(r'https?://', url):
        return bot.reply_to(msg, "⚠️ أرسل رابطًا صحيحًا يبدأ بـ http أو https")

    wait_msg = bot.reply_to(msg, "🔎 **جارٍ تحليل الرابط...**", parse_mode="Markdown")
    info = get_media_info(url)

    if "error" in info:
        return bot.edit_message_text(
            f"❌ **فشل جلب المعلومات:** {info['error']}",
            msg.chat.id, wait_msg.message_id, parse_mode="Markdown"
        )

    title = info.get("title", "بدون عنوان")
    duration = info.get("duration", 0)
    uploader = info.get("uploader", "غير معروف")
    site = info.get("extractor", "منصة غير معروفة")

    caption = (
        f"🎬 **العنوان:** {title}\n"
        f"📺 **المنصة:** {site}\n"
        f"👤 **الناشر:** {uploader}\n"
        f"⏱️ **المدة:** {int(duration // 60)}:{int(duration % 60):02d}\n\n"
        f"👇 اختر نوع التحميل:"
    )

    markup = InlineKeyboardMarkup()
    unique = str(hash(url) % 1000000)
    markup.add(
        InlineKeyboardButton("📹 تحميل فيديو", callback_data=f"video|{unique}|{url}"),
        InlineKeyboardButton("🎵 تحميل صوت", callback_data=f"audio|{unique}|{url}")
    )

    bot.edit_message_text(caption, msg.chat.id, wait_msg.message_id, reply_markup=markup, parse_mode="Markdown")

# ===========================
# 🎯 التعامل مع الأزرار
# ===========================
@bot.callback_query_handler(func=lambda call: True)
def button_handler(call):
    try:
        action, uid, url = call.data.split("|", 2)
    except:
        return bot.answer_callback_query(call.id, "⚠️ حدث خطأ في البيانات")

    bot.answer_callback_query(call.id, "✅ جاري التحميل...")
    status = bot.send_message(call.message.chat.id, "⏳ **يتم التحميل الآن...**", parse_mode="Markdown")

    file_name = f"{call.message.chat.id}_{uid}"
    file_path = download_media(url, action, file_name)

    bot.delete_message(call.message.chat.id, status.message_id)

    if not file_path:
        return bot.send_message(call.message.chat.id, "❌ **فشل التحميل.** الرابط ربما خاص أو غير مدعوم.")

    try:
        with open(file_path, "rb") as f:
            if action == "audio":
                bot.send_audio(call.message.chat.id, f, caption="🎵 تم التحميل بنجاح!", parse_mode="Markdown")
            else:
                bot.send_video(call.message.chat.id, f, caption="📹 تم التحميل بنجاح!", parse_mode="Markdown", supports_streaming=True)
    except Exception as e:
        bot.send_message(call.message.chat.id, f"❌ **خطأ أثناء الإرسال:** {e}")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

# ===========================
# 🌐 Flask endpoint
# ===========================
@app.route('/')
def home():
    return "✅ البوت يعمل بنجاح!"

# ===========================
# 🏁 تشغيل السيرفر والبوت
# ===========================
def run_bot():
    try:
        bot.delete_webhook()
    except:
        pass
    bot.infinity_polling(skip_pending=True)

if __name__ == "__main__":
    from waitress import serve
    Thread(target=run_bot).start()
    port = int(os.environ.get("PORT", 5000))
    print(f"🌐 Server running on port {port}")
    serve(app, host="0.0.0.0", port=port)
