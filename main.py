import os
import threading
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from yt_dlp import YoutubeDL

# -------------------------------------------------------------
# 1. خادم الويب للإبقاء على الخدمة شغالة 24/7
# -------------------------------------------------------------
app_web = Flask(__name__)

@app_web.route('/')
def home():
    return "Bot is running perfectly!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app_web.run(host='0.0.0.0', port=port)

# -------------------------------------------------------------
# 2. التوكن الخاص بك
# -------------------------------------------------------------
TOKEN = "8859717725:AAFt9FWRA5kkmzZSNsUjQ1qv79l9kSR4i4Q"

# -------------------------------------------------------------
# 3. أوامر ودوال البوت
# -------------------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 أهلاً بك!\n"
        "أرسل لي رابط أي فيديو من يوتيوب وسأقوم بتحميله لك فوراً."
    )

async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    
    if not url.startswith("http://") and not url.startswith("https://"):
        await update.message.reply_text("❌ الرجاء إرسال رابط صحيح يبدأ بـ http أو https.")
        return

    status_msg = await update.message.reply_text("⏳ جاري جلب وتحميل الفيديو، يرجى الانتظار...")
    
    filename = "downloaded_video.mp4"
    if os.path.exists(filename):
        os.remove(filename)

    # خيارات متطورة لتجاوز حظر يوتيوب المباشر على السيرفرات السحابية
    ydl_opts = {
        'format': 'b[height<=360]/b[height<=480]/b/best',
        'outtmpl': filename,
        'nocheckcertificate': True,
        'ignoreerrors': True,
        'no_warnings': True,
        'quiet': True,
        'retries': 10,
        'fragment_retries': 10,
        # التمويه التام كعميل iOS/Android لتجاوز اختبار البوت
        'extractor_args': {
            'youtube': {
                'player_client': ['ios', 'mweb', 'android'],
                'skip': ['hls', 'dash']
            }
        },
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1',
            'Accept-Language': 'en-US,en;q=0.9',
        }
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        if os.path.exists(filename) and os.path.getsize(filename) > 0:
            await status_msg.edit_text("⬆️ جاري رفع الفيديو إلى تليجرام...")
            with open(filename, 'rb') as video:
                await update.message.reply_video(video)
            os.remove(filename)
            await status_msg.delete()
        else:
            await status_msg.edit_text("❌ تعذر تحميل الفيديو. قد يكون الحجم كبيراً جداً أو المقطع خاص.")
            
    except Exception as e:
        await status_msg.edit_text("❌ حدث خطأ غير متوقع أثناء التحميل.")
        if os.path.exists(filename):
            os.remove(filename)

# -------------------------------------------------------------
# 4. تشغيل الخادم والبوت
# -------------------------------------------------------------
if __name__ == '__main__':
    threading.Thread(target=run_flask, daemon=True).start()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))
    print("Bot started...")
    app.run_polling()
