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
# 1. السيرفر الوهمي لمنصة Render (الخطة المجانية)
# =========================================================


class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):

  def do_GET(self):
    self.send_response(200)
    self.end_headers()
    self.wfile.write(b'YouTube Downloader Bot is running!')


def run_dummy_server():
  port = int(os.environ.get('PORT', 8080))
  server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
  server.serve_forever()


Thread(target=run_dummy_server, daemon=True).start()

# =========================================================
# 2. إعدادات اللوج والبوت
# =========================================================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
)

TELEGRAM_BOT_TOKEN = os.environ.get(
    'BOT_TOKEN', '8859717725:AAFt9FWRA5kkmzZSNsUjQ1qv79l9kSR4i4Q'
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
  """أمر البداية /start"""
  await update.message.reply_text(
      'أهلاً بك! 👋\nأرسل لي رابط أي فيديو أو مقطع Shorts من **يوتيوب** (أو'
      ' من باقي وسائل التواصل الاجتماعي) وسأقوم بتحميله لك فوراً! 🎬'
  )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
  """معالجة وتنزيل فيديوهات يوتيوب والمنصات الأخرى"""
  url = update.message.text.strip()

  if not url.startswith(('http://', 'https://')):
    await update.message.reply_text('من فضلك أرسل رابطاً صحيحاً للفيديو.')
    return

  msg = await update.message.reply_text(
      'جاري التوصيل بيوتيوب وتحميل الفيديو... ⏳'
  )
  output_filename = f'youtube_{update.message.message_id}.mp4'

  # إعدادات مخصصة لضمان جلب أفضل صيغة MP4 متوافقة مع تليجرام وبدون مشاكل في يوتيوب
  ydl_opts = {
      'format': (
          'bestvideo[ext=mp4][vcodec^=avc1]+bestaudio[ext=m4a]/best[ext=mp4]/best'
      ),
      'outtmpl': output_filename,
      'quiet': True,
      'no_warnings': True,
      'max_filesize': 50
      * 1024
      * 1024,  # أقصى حجم 50 ميجابايت كحد أقصى للبوت العادي
      'user_agent': (
          'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,'
          ' like Gecko) Chrome/120.0.0.0 Safari/537.36'
      ),
  }

  try:
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
      info = ydl.extract_info(url, download=True)
      video_title = info.get('title', 'فيديو يوتيوب')

    # إرسال الفيديو للعميل
    await update.message.reply_video(
        video=open(output_filename, 'rb'),
        caption=f'🎬 **{video_title}**\n\nتم التحميل بنجاح عبر البوت! ✨',
        parse_mode='Markdown',
    )
    await msg.delete()

  except Exception as e:
    logging.error(f'YouTube Download Error: {e}')
    error_message = (
        'حدث خطأ أثناء تحميل الفيديو.\n'
        '• تأكد من صحة الرابط.\n'
        '• إذا كان حجم الفيديو يتجاوز 50 ميجابايت فلن يمكن إرساله عبر تليجرام.'
    )
    await msg.edit_text(error_message)

  finally:
    # تنظيف الملفات بعد الانتهاء
    if os.path.exists(output_filename):
      os.remove(output_filename)


# =========================================================
# 3. تشغيل البوت
# =========================================================
if __name__ == '__main__':
  app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

  app.add_handler(CommandHandler('start', start))
  app.add_handler(
      MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
  )

  print('YouTube Downloader Bot is polling...')
  app.run_polling()
