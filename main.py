import logging
import os
import asyncio
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

# ===================================================
# 1. السيرفر الوهمي لتجاوز مشكلة Port في Render
# ===================================================
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

# ===================================================
# 2. إعدادات السجلات والتوكين
# ===================================================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TOKEN = os.environ.get("8859717725:AAFt9FWRA5kkmzZSNsUjQ1qv79l9kSR4i4Q")

# ===================================================
# 3. دالة تنزيل الفيديو باستخدام yt-dlp
# ===================================================
def download_video(url, output_path):
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
        'merge_output_format': 'mp4',
        
        # تجاوز حظر السيرفرات والتأكد من عدم طلب تسجيل الدخول
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'ios']
            }
        },
        'noplaylist': True,
        'quiet': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        return filename

# ===================================================
# 4. معالجات الأوامر والرسائل
# ===================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أهلاً بك! أرسل لي رابط فيديو من يوتيوب وسأقوم بتحميله وإرساله لك مباشرة.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    
    if not (url.startswith("http://") or url.startswith("https://")):
        await update.message.reply_text("الرجاء إرسال رابط صحيح.")
        return

    status_msg = await update.message.reply_text("⏳ جاري جلب الفيديو والتحميل...")

    download_dir = "downloads"
    os.makedirs(download_dir, exist_ok=True)

    file_path = None
    try:
        # تشغيل دالة التنزيل داخل loop بدون إيقاف البوت
        loop = asyncio.get_event_loop()
        file_path = await loop.run_in_executor(None, download_video, url, download_dir)

        await status_msg.edit_text("⬆️ جاري إرسال الفيديو إلى التلغرام...")

        # إرسال الفيديو للمستخدم
        with open(file_path, 'rb') as video_file:
            await update.message.reply_video(video=video_file)

        await status_msg.delete()

    except Exception as e:
        logging.error(f"Error downloading/sending: {e}")
        await status_msg.edit_text("حدث خطأ أثناء تحميل الفيديو. تأكد من أن الرابط يعمل وأن حجم الفيديو غير ضخم جداً.")

    finally:
        # تنظيف الملفات بعد إرسالها لتوفير المساحة في Render
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass

# ===================================================
# 5. تشغيل البوت
# ===================================================
if __name__ == '__main__':
    if not TOKEN:
        raise ValueError("لم يتم العثور على BOT_TOKEN في متغيرات البيئة!")

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("البوت يعمل الآن...")
    app.run_polling()
