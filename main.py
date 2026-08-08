import os
import threading
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from yt_dlp import YoutubeDL

# -------------------------------------------------------------
# 1. إنشاء خادم ويب خفيف لإبقاء منصة الاستضافة شغالة 24/7
# -------------------------------------------------------------
app_web = Flask(__name__)

@app_web.route('/')
def home():
    return "Bot is running smoothly!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app_web.run(host='0.0.0.0', port=port)

# -------------------------------------------------------------
# 2. توكن البوت الخاص بك
# -------------------------------------------------------------
TOKEN = "8859717725:AAFt9FWRA5kkmzZSNsUjQ1qv7919kSR4i4Q"

# -------------------------------------------------------------
# 3. أوامر ودوال البوت
# -------------------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 أهلاً بك!\n"
        "أرسل لي رابط أي فيديو من يوتيوب أو أي موقع آخر وسأقوم بتحميله وإرساله لك فوراً."
    )

async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    
    # التأكد من صحة الرابط
    if not url.startswith("http://") and not url.startswith("https://"):
        await update.message.reply_text("❌ الرجاء إرسال رابط صحيح يبدأ بـ http أو https.")
        return

    status_msg = await update.message.reply_text("⏳ جاري جلب وتحميل الفيديو، يرجى الانتظار...")
    
    # خيارات yt-dlp الذكية (تحميل بجودة 480p/360p لتفادي مشاكل الحجم ومرورها بنجاح)
    ydl_opts = {
        'format': 'b[height<=480]/b[height<=360]/b',
        'outtmpl': 'downloaded_video.%(ext)s',
        'nocheckcertificate': True,
        'ignoreerrors': True,
        'no_warnings': True,
        'quiet': True,
        'retries': 10,
        'fragment_retries': 10,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
        }
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
        
        # إرسال الفيديو للمستخدم
        await status_msg.edit_text("⬆️ جاري رفع الفيديو إلى تليجرام...")
        with open(filename, 'rb') as video:
            await update.message.reply_video(video)
            
        # التنظيف وإلغاء الملف المؤقت
        if os.path.exists(filename):
            os.remove(filename)
        await status_msg.delete()
        
    except Exception as e:
        await status_msg.edit_text("❌ حدث خطأ أثناء التحميل. تأكد من صحة الرابط وأن الفيديو ليس خاصاً.")

# -------------------------------------------------------------
# 4. تشغيل الخادم والبوت
# -------------------------------------------------------------
if __name__ == '__main__':
    # تشغيل خادم الويب في الخلفية
    threading.Thread(target=run_flask, daemon=True).start()
    
    # تشغيل بوت تليجرام
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))
    
    print("Bot starting...")
    app.run_polling()
