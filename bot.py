#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import subprocess
import telebot

# ===========================
# 🔹 توكن البوت (مضمّن في الكود)
# ===========================
BOT_TOKEN = "8461219655:AAF1jnw_IpKuu1tdXJSW9ubnjRe5pxlMoxo"

# إنشاء كائن البوت
bot = telebot.TeleBot(BOT_TOKEN)

# ===========================
# 📥 دالة تحميل فيديو من TikTok
# ===========================
def download_tiktok(url: str) -> bool:
    """
    تحميل الفيديو من TikTok وحفظه باسم video.mp4
    """
    command = f"yt-dlp -f best --quiet --no-warnings -o video.mp4 '{url}'"
    os.system(command)
    return os.path.exists("video.mp4")

# ===========================
# ✨ دالة إضافة توقيع ذهبي على الفيديو
# ===========================
def add_signature(input_file: str, output_file: str, text: str = "Tarzanbot") -> None:
    """
    إضافة نص توقيع على الفيديو باستخدام ffmpeg
    """
    command = [
        "ffmpeg", "-i", input_file,
        "-vf", f"drawtext=text='{text}':fontcolor=gold:fontsize=40:box=1:boxcolor=black@0.3:boxborderw=5:x=w-tw-20:y=h-th-20",
        "-codec:a", "copy", output_file, "-y"
    ]
    subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# ===========================
# ⚡ أوامر البوت
# ===========================

@bot.message_handler(commands=['start'])
def start_handler(msg):
    bot.reply_to(msg, "👋 أهلاً بك!\nأرسل رابط فيديو TikTok وسأقوم بتحميله مع توقيع Tarzanbot ✨")

@bot.message_handler(func=lambda msg: True)
def handle_message(msg):
    url = msg.text.strip()
    
    if "tiktok.com" not in url:
        bot.reply_to(msg, "⚠️ أرسل رابط TikTok صالح.")
        return

    bot.reply_to(msg, "⏳ جاري تحميل الفيديو، انتظر قليلاً...")

    try:
        # تحميل الفيديو
        if not download_tiktok(url):
            bot.reply_to(msg, "❌ فشل التحميل.")
            return

        bot.reply_to(msg, "🎨 جاري إضافة توقيع Tarzanbot...")
        add_signature("video.mp4", "signed.mp4", "Tarzanbot")

        # إرسال الفيديو بعد التوقيع
        with open("signed.mp4", "rb") as vid:
            bot.send_video(msg.chat.id, vid, caption="✅ تم التحميل مع توقيع Tarzanbot ✨")

    except Exception as e:
        bot.reply_to(msg, f"❌ حدث خطأ: {e}")

    finally:
        # تنظيف الملفات المؤقتة
        for f in ["video.mp4", "signed.mp4"]:
            if os.path.exists(f):
                os.remove(f)

# ===========================
# 🟢 تشغيل البوت
# ===========================

if __name__ == "__main__":
    print("🤖 Tarzanbot is running...")
    bot.infinity_polling()
