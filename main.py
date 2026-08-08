import os
import threading
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from yt_dlp import YoutubeDL

# -------------------------------------------------------------
# 1. خادم الويب للإبقاء على الخدمة شغالة 24/7 على منصة الاستضافة
# -------------------------------------------------------------
app_web = Flask(__name__)

@app_web.route('/')
def home():
    return "Bot is running perfectly!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app_web.run(host='0.0.0.0', port=port)

# -------------------------------------------------------------
# 2. التوكن الخاص بالبوت
# -------------------------------------------------------------
TOKEN = "8859717725:AAFt9FWRA5kkmzZSNsUjQ1qv79l9kSR4i4Q"

# -------------------------------------------------------------
# 3. أوامر ودوال البوت
# -------------------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 أهلاً بك!\n"
        "أرسل لي رابط أي فيديو من يوتيوب وسأقوم بتحميله لك فوراً بحجم خفيف ومناسب."
    )

async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    
    # التأكد من صحة الرابط
    if not url.startswith("http://") and not url.startswith("https://"):
        await update.message.reply_text("❌ الرجاء إرسال رابط صحيح يبدأ بـ http أو https.")
        return

    status_msg = await update.message.reply_text("⏳ جاري جلب وتحميل الفيديو، يرجى الانتظار...")
    
    filename = "downloaded_video.mp4"
    if os.path.exists(filename):
        try:
            os.remove(filename)
        except Exception:
            pass

    # خيارات تضمن اختيار جودة منخفضة (360p/240p) ليبقى الحجم أقل من 50MB
    ydl_opts = {
        'format': 'worstvideo[ext=mp4]+worstaudio[ext=m4a]/worst[ext=mp4]/worst',
        'outtmpl': filename,
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'no_warnings': True,
        'quiet': True,
        'retries': 5,
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'ios', 'mweb']
            }
        },
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
        }
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        # التأكد من وجود الملف وأن حجمه لا يتجاوز حد تليجرام (50 ميجابايت)
        if os.path.exists(filename) and os.path.getsize(filename) > 0:
            file_size_mb = os.path.getsize(filename) / (1024 * 1024)
            
            if file_size_mb > 49:
                await status_msg.edit_text("❌ اعتذار: حجم الملف بعد الضغط ما زال يتجاوز 50 ميجابايت (الحد الأقصى لتليجرام).")
                os.remove(filename)
                return

            await status_msg.edit_text("⬆️ جاري رفع الفيديو إلى تليجرام...")
            with open(filename, 'rb') as video:
                await update.message.reply_video(video)
            
            os.remove(filename)
            await status_msg.delete()
        else:
            await status_msg.edit_text("❌ تعذر إنشاء ملف الفيديو، تأكد من صحة الرابط.")
            
    except Exception as e:
        error_details = str(e)[:150]
        await status_msg.edit_text(f"❌ حدث خطأ أثناء التحميل:\n`{error_details}`", parse_mode="Markdown")
        if os.path.exists(filename):
            try:
                os.remove(filename)
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
