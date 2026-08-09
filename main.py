import logging
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
import yt_dlp
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# =========================================================
# 1. السيرفر الوهمي لتجاوز مشكلة Port في Render
# =========================================================
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is active and running!")

def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

Thread(target=run_dummy_server, daemon=True).start()

# =========================================================
# 2. إعدادات البوت والتحميل
# =========================================================
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

# جلب التوكن من Environment Variables في Render
TOKEN = os.environ.get("8859717725:AAFt9FWRA5kkmzZSNsUjQ1qv79l9kSR4i4Q")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("مرحباً! أرسل لي رابط فيديو من يوتيوب أو أي منصة وسأقوم بتحميله لك.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    if not url.startswith("http"):
        return

    status_msg = await update.message.reply_text("جاري تحميل الفيديو... ⏳")
    filename = f"video_{update.message.message_id}.mp4"

    # إعدادات yt-dlp المتطورة لتجاوز الحظر
    ydl_opts = {
        'format': 'bestvideo[ext=mp4][vcodec^=avc1]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': filename,
        'max_filesize': 50 * 1024 * 1024, # 50MB (حد التليجرام)
        'extractor_args': {'youtube': {'player_client': ['android']}}, # الحل الجذري للحظر
        'quiet': True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        await update.message.reply_video(video=open(filename, 'rb'), caption="تم التحميل بنجاح! ✅")
        await status_msg.delete()
    except Exception as e:
        await status_msg.edit_text(f"خطأ: الفيديو قد يكون كبيراً جداً أو خاصاً.\nالتفاصيل: {e}")
    finally:
        if os.path.exists(filename):
            os.remove(filename)

if __name__ == '__main__':
    if not TOKEN:
        print("خطأ: يرجى وضع BOT_TOKEN في إعدادات Render")
    else:
        app = ApplicationBuilder().token(TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        print("البوت يعمل الآن...")
        app.run_polling()
