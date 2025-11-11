#!/bin/bash
# تثبيت ffmpeg على Render
apt-get update
apt-get install -y ffmpeg

# تشغيل البوت
python3 bot.py
