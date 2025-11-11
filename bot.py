import telebot
import os
import subprocess

BOT_TOKEN = os.environ.get("8461219655:AAF1jnw_IpKuu1tdXJSW9ubnjRe5pxlMoxo")  # ضع توكن البوت في Render Environment

bot = telebot.TeleBot(BOT_TOKEN)

# 📥 دالة تحميل الفيديو من TikTok
def download_tiktok(url):
    os.system(f"yt-dlp -f best --quiet --no-warnings -o video.mp4 '{url}'")
    return os.path.exists("video.mp4")

# ✨ دالة لإضافة توقيع ذهبي باستخدام ffmpeg
def add_signature(input_file, output_file, text="Tarzanbot"):
    command = [
        "ffmpeg", "-i", input_file,
        "-vf", f"drawtext=text='{text}':fontcolor=gold:fontsize=40:box=1:boxcolor=black@0.3:boxborderw=5:x=w-tw-20:y=h-th-20",
        "-codec:a", "copy", output_file, "-y"
    ]
    subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

@bot.message_handler(commands=['start'])
def start(msg):
    bot.reply_to(msg, "👋 أهلاً بك!\nأرسل رابط فيديو TikTok وسأحمله لك مع توقيع Tarzanbot ✨")

@bot.message_handler(func=lambda msg: True)
def handle_message(msg):
    url = msg.text.strip()
    if "tiktok.com" not in url:
        bot.reply_to(msg, "⚠️ أرسل رابط TikTok صالح.")
        return

    bot.reply_to(msg, "⏳ جاري تحميل الفيديو، انتظر قليلاً...")

    try:
        if not download_tiktok(url):
            bot.reply_to(msg, "❌ فشل التحميل.")
            return

        bot.reply_to(msg, "🎨 جاري إضافة توقيع Tarzanbot...")
        add_signature("video.mp4", "signed.mp4", "Tarzanbot")

        with open("signed.mp4", "rb") as vid:
            bot.send_video(msg.chat.id, vid, caption="✅ تم التحميل مع توقيع Tarzanbot ✨")

    except Exception as e:
        bot.reply_to(msg, f"❌ حدث خطأ: {e}")
    finally:
        for f in ["video.mp4", "signed.mp4"]:
            if os.path.exists(f):
                os.remove(f)

print("🤖 Tarzanbot is running...")
bot.polling()
