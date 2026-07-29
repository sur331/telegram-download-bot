import os
import glob
from threading import Thread
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp

app_web = Flask('')

@app_web.route('/')
def home():
    return "Bot is running perfectly!"

def run_web():
    app_web.run(host='0.0.0.0', port=8080)

# ضع التوكن الخاص بك هنا
TOKEN = "8859717725:AAFt9FWRA5kkmzZSNsUjQ1qv79l9kSR4i4Q"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('أهلاً بك! أرسل لي رابط فيديو من يوتيوب أو إنستغرام لتحميله.')

async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    if not url.startswith(('http://', 'https://')):
        return

    msg = await update.message.reply_text('⏳ جاري جلب الفيديو والتحميل، يرجى الانتظار...')
    
    # اسم ملف مؤقت فريد لتجنب التضارب
    output_template = f"video_{update.message.message_id}.%(ext)s"

    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': output_template,
        'max_filesize': 50 * 1024 * 1024,  # حد أقصى 50 ميجابايت لتلجرام
        'quiet': True,
        'no_warnings': True,
        # محاكاة متصفح حقيقي لتجاوز الحظر على Render
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'referer': 'https://www.google.com/',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        # البحث عن الملف الذي تم تحميله
        downloaded_files = glob.glob(f"video_{update.message.message_id}.*")
        
        if downloaded_files:
            file_path = downloaded_files[0]
            with open(file_path, 'rb') as video:
                await update.message.reply_video(video=video, caption="تم التحميل بنجاح ✨")
            os.remove(file_path)
            await msg.delete()
        else:
            await msg.edit_text('❌ تعذر العثور على الملف بعد التحميل.')

    except Exception as e:
        error_text = str(e)
        if "File is larger than" in error_text or "max_filesize" in error_text:
            await msg.edit_text('⚠️ حجم الفيديو كبير جداً (يتجاوز 50 ميجابايت)، لا يمكن إرساله عبر تلجرام.')
        else:
            await msg.edit_text('❌ حدث خطأ أثناء التحميل. قد يكون الرابط خاصاً أو محظوراً من السيرفر.')

if __name__ == '__main__':
    Thread(target=run_web).start()
    
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))
    app.run_polling()
