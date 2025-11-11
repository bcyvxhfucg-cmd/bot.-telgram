#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import subprocess
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import json

# ===========================
# 🔹 توكن البوت (مضمّن في الكود)
# ===========================
BOT_TOKEN = "8461219655:AAF1jnw_IpKuu1tdXJSW9ubnjRe5pxlMoxo"

# إنشاء كائن البوت
bot = telebot.TeleBot(BOT_TOKEN)

# ===========================
# 📥 دالة تحميل معلومات الفيديو
# ===========================
def get_video_info(url: str) -> dict:
    """
    الحصول على معلومات الفيديو من TikTok باستخدام yt-dlp
    """
    command = f"yt-dlp -j '{url}'"
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        return {}
    try:
        info = json.loads(result.stdout)
        return info
    except json.JSONDecodeError:
        return {}

# ===========================
# 📥 دالة تحميل الفيديو أو الصوت
# ===========================
def download_tiktok(url: str, format_type: str = "video") -> str:
    """
    تحميل الفيديو أو الصوت من TikTok
    """
    output_file = "output.mp4" if format_type == "video" else "output.mp3"
    fmt = "best" if format_type == "video" else "bestaudio"
    command = f"yt-dlp -f {fmt} --quiet --no-warnings -o {output_file} '{url}'"
    os.system(command)
    return output_file if os.path.exists(output_file) else ""

# ===========================
# ⚡ أوامر البوت
# ===========================

@bot.message_handler(commands=['start'])
def start_handler(msg):
    bot.reply_to(msg, "👋 أهلاً بك!\nأرسل رابط فيديو TikTok وسأقوم بتحميله لك ✨")

@bot.message_handler(func=lambda msg: True)
def handle_message(msg):
    url = msg.text.strip()
    
    if "tiktok.com" not in url:
        bot.reply_to(msg, "⚠️ أرسل رابط TikTok صالح.")
        return

    bot.reply_to(msg, "⏳ جاري جلب معلومات الفيديو...")
    info = get_video_info(url)
    
    if not info:
        bot.reply_to(msg, "❌ فشل جلب معلومات الفيديو.")
        return
    
    # إعداد رسالة المعلومات
    caption = (
        f"👤 المستخدم: {info.get('uploader', 'غير متوفر')}\n"
        f"❤️ الإعجابات: {info.get('like_count', '0')}\n"
        f"💬 التعليقات: {info.get('comment_count', '0')}\n"
        f"🔁 المشاركات: {info.get('share_count', '0')}\n"
        f"🎵 الصوت: {info.get('track', 'غير متوفر')}\n"
        f"📌 عنوان: {info.get('title', 'غير متوفر')}"
    )

    # إنشاء أزرار التحميل
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("📹 تحميل الفيديو", callback_data=f"video|{url}"),
        InlineKeyboardButton("🎵 تحميل الصوت", callback_data=f"audio|{url}")
    )

    bot.send_message(msg.chat.id, caption, reply_markup=markup)

# ===========================
# 🎯 التعامل مع الضغط على الأزرار
# ===========================

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    action, url = call.data.split("|")
    msg = call.message
    bot.edit_message_reply_markup(msg.chat.id, msg.message_id, reply_markup=None)
    bot.send_message(msg.chat.id, "⏳ جاري التحميل...")

    file_path = download_tiktok(url, format_type="video" if action == "video" else "audio")

    if not file_path:
        bot.send_message(msg.chat.id, "❌ فشل التحميل.")
        return

    # إرسال الملف مباشرة دون أي توقيع
    if action == "video":
        with open(file_path, "rb") as vid:
            bot.send_video(msg.chat.id, vid, caption="✅ تم تحميل الفيديو ✨")
    else:
        with open(file_path, "rb") as aud:
            bot.send_audio(msg.chat.id, aud, caption="✅ تم تحميل الصوت ✨")

    os.remove(file_path)

# ===========================
# 🟢 تشغيل البوت
# ===========================

if __name__ == "__main__":
    print("🤖 Tarzanbot is running...")
    bot.infinity_polling()
