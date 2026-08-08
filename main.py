import os
import threading
import requests
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# -------------------------------------------------------------
# 1. خادم الويب لإبقاء منصة الاستضافة شغالة 24/7
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
        "أرسل لي رابط أي فيديو من يوتيوب وسأقوم بتحميله وإرساله لك فوراً."
    )

async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    
    if not url.startswith("http://") and not url.startswith("https://"):
        await update.message.reply_text("❌ الرجاء إرسال رابط صحيح يبدأ بـ http أو https.")
        return

    status_msg = await update.message.reply_text("⏳ جاري جلب الفيديو وتجاوز الحظر، يرجى الانتظار...")
    
    # استخدام Cobalt API لتجاوز حظر IP يوتيوب
    api_url = "https://api.cobalt.tools/api/json"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    payload = {
        "url": url,
        "videoQuality": "480"  # جودة ممتازة وسريعة في التحميل ولن تتجاوز مساحة تليجرام
    }

    try:
        response = requests.post(api_url, json=payload, headers=headers)
        data = response.json()

        if data.get("status") in ["stream", "redirect"]:
            video_url = data.get("url")
            
            # تحميل ملف الفيديو مؤقتاً
            video_data = requests.get(video_url, stream=True)
            filename = "downloaded_video.mp4"
            
            with open(filename, 'wb') as f:
                for chunk in video_data.iter_content(chunk_size=1024*1024):
                    if chunk:
                        f.write(chunk)

            await status_msg.edit_text("⬆️ جاري رفع الفيديو إلى تليجرام...")
            
            with open(filename, 'rb') as video:
                await update.message.reply_video(video)
                
            if os.path.exists(filename):
                os.remove(filename)
                
            await status_msg.delete()
        else:
            await status_msg.edit_text("❌ تعذر جلب الفيديو، قد يكون المقطع خاصاً أو يتطلب تسجيل دخول.")

    except Exception as e:
        await status_msg.edit_text(f"❌ حدث خطأ أثناء التحميل: {str(e)[:100]}")

# -------------------------------------------------------------
# 4. تشغيل الخادم والبوت
# -------------------------------------------------------------
if __name__ == '__main__':
    threading.Thread(target=run_flask, daemon=True).start()
    
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))
    
    print("Bot starting...")
    app.run_polling()
