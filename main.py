import os
import threading
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from pytubefix import YouTube

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
TOKEN = "8859717725:AAFt9FWRA5kkmzZSNsUjQ1qv7919kSR4i4Q"

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
    
    try:
        # استخدام pytubefix المحسنة لتجاوز قيود يوتيوب والبوتات (Android client)
        yt = YouTube(url, client='ANDROID')
        
        # اختيار أقل جودة مدمجة (360p) لضمان أن الحجم صغير جداً ومناسب لتليجرام
        stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').first()
        
        if not stream:
            stream = yt.streams.filter(file_extension='mp4').first()

        filename = stream.download(filename="downloaded_video.mp4")
        
        file_size_mb = os.path.getsize(filename) / (1024 * 1024)
        if file_size_mb > 49:
            await status_msg.edit_text("❌ الفيديو مدته طويلة جداً وحجمه يتجاوز 50 ميجابايت (حد تليجرام المسموح).")
            os.remove(filename)
            return

        await status_msg.edit_text("⬆️ جاري رفع الفيديو إلى تليجرام...")
        with open(filename, 'rb') as video:
            await update.message.reply_video(video)
        
        if os.path.exists(filename):
            os.remove(filename)
        await status_msg.delete()

    except Exception as e:
        error_details = str(e)[:150]
        await status_msg.edit_text(f"❌ تعذر التحميل:\n`{error_details}`", parse_mode="Markdown")
        if os.path.exists("downloaded_video.mp4"):
            try:
                os.remove("downloaded_video.mp4")
            except Exception:
                pass

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
