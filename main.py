import os
import threading
import requests
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# -------------------------------------------------------------
# 1. خادم الويب لإبقاء الخدمة شغالة 24/7
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
TOKEN = "8859717725:AAFt9FWRA5kkmzZSNsUjQ1qv7919kSR4i4Q"

# -------------------------------------------------------------
# 3. أوامر ودوال البوت (تجاوز حظر Render عبر الوسيط)
# -------------------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 أهلاً بك!\n"
        "أرسل لي رابط أي فيديو من يوتيوب وسأقوم بتحميله وإرساله لك فوراً."
    )

async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    
    if not url.startswith("http://") and not url.startswith("https://"):
        await update.message.reply_text("❌ الرجاء إرسال رابط صحيح يبدأ بـ http أو https.")
        return

    status_msg = await update.message.reply_text("⏳ جاري جلب الفيديو وتجاوز الحظر، يرجى الانتظار...")
    filename = "downloaded_video.mp4"

    try:
        # استخدام خدمة وسيطة لتجاوز حظر يوتيوب لـ Render
        download_api_url = f"https://api.vkrdown.com/v4/youtube?url={url}"
        response = requests.get(download_api_url, timeout=15).json()

        video_download_url = None

        # البحث عن أسرع جودة خفيفة (360p أو 480p) تناسب تليجرام
        if "data" in response and "downloads" in response["data"]:
            for item in response["data"]["downloads"]:
                if item.get("extension") == "mp4" and item.get("url"):
                    video_download_url = item["url"]
                    # تفضيل الجودة المتوسطة لخفة الحجم
                    if "360" in item.get("quality", "") or "480" in item.get("quality", ""):
                        break

        if not video_download_url and "data" in response and "url" in response["data"]:
            video_download_url = response["data"]["url"]

        if not video_download_url:
            await status_msg.edit_text("❌ تعذر استخراج رابط الفيديو، تأكد من صحة الرابط.")
            return

        # تنزيل الملف مؤقتاً على السيرفر
        video_res = requests.get(video_download_url, stream=True, timeout=60)
        with open(filename, 'wb') as f:
            for chunk in video_res.iter_content(chunk_size=1024*1024):
                if chunk:
                    f.write(chunk)

        file_size_mb = os.path.getsize(filename) / (1024 * 1024)
        if file_size_mb > 49:
            await status_msg.edit_text("❌ الفيديو مدته طويلة وحجمه يتجاوز الحد المسموح في تليجرام (50MB).")
            os.remove(filename)
            return

        await status_msg.edit_text("⬆️ جاري رفع الفيديو إلى تليجرام...")
        with open(filename, 'rb') as video:
            await update.message.reply_video(video)
            
        if os.path.exists(filename):
            os.remove(filename)
        await status_msg.delete()

    except Exception as e:
        await status_msg.edit_text("❌ حدث خطأ أثناء التحميل، يرجى المحاولة لاحقاً.")
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
    print("Bot is active...")
    app.run_polling()
