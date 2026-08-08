import os
import threading
import requests
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# -------------------------------------------------------------
# 1. خادم الويب
# -------------------------------------------------------------
app_web = Flask(__name__)

@app_web.route('/')
def home():
    return "Bot is active!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app_web.run(host='0.0.0.0', port=port)

# -------------------------------------------------------------
# 2. التوكن الخاص بك
# -------------------------------------------------------------
TOKEN = "8859717725:AAFt9FWRA5kkmzZSNsUjQ1qv7919kSR4i4Q"

# -------------------------------------------------------------
# 3. دالة التحميل المتقدمة (Invidious Engine)
# -------------------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 أهلاً بك!\nأرسل لي رابط الفيديو من يوتيوب وسأقوم بتحميله فوراً دون حظر."
    )

def extract_video_id(url):
    """استخراج ID الفيديو من رابط يوتيوب"""
    if "v=" in url:
        return url.split("v=")[1].split("&")[0]
    elif "youtu.be/" in url:
        return url.split("youtu.be/")[1].split("?")[0]
    return None

async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    video_id = extract_video_id(url)

    if not video_id:
        await update.message.reply_text("❌ الرابط غير صحيح، يرجى إرسال رابط يوتيوب مباشر.")
        return

    status_msg = await update.message.reply_text("⏳ جاري استخراج الفيديو وتجاوز الحظر...")

    # قائمة بخوادم Invidious المستقرة للتناوب في حال حظر أحدها
    invidious_instances = [
        "https://inv.nadeko.net",
        "https://invidious.nerdvpn.de",
        "https://invidious.no-booster.eu"
    ]

    download_success = False
    filename = "downloaded_video.mp4"

    for instance in invidious_instances:
        try:
            api_url = f"{instance}/api/v1/videos/{video_id}"
            res = requests.get(api_url, timeout=10)
            
            if res.status_code == 200:
                data = res.json()
                format_streams = data.get("formatStreams", [])
                
                # البحث عن أسرع جودة خفيفة متوافقة مع تليجرام (360p/480p)
                video_download_url = None
                for stream in format_streams:
                    if stream.get("container") == "mp4":
                        video_download_url = stream.get("url")
                        break
                
                if not video_download_url and format_streams:
                    video_download_url = format_streams[0].get("url")

                if video_download_url:
                    # تنزيل الملف مجزأ لتفادي حظر الحجم وقطع الاتصال
                    with requests.get(video_download_url, stream=True, timeout=60) as r:
                        r.raise_for_status()
                        with open(filename, 'wb') as f:
                            for chunk in r.iter_content(chunk_size=1024*1024):
                                f.write(chunk)
                    download_success = True
                    break
        except Exception as e:
            continue

    if download_success:
        try:
            await status_msg.edit_text("⬆️ جاري رفع الفيديو إلى تليجرام...")
            with open(filename, 'rb') as video:
                await update.message.reply_video(video)
            
            if os.path.exists(filename):
                os.remove(filename)
            await status_msg.delete()
        except Exception:
            await status_msg.edit_text("❌ حدث خطأ أثناء رفع الفيديو لتليجرام، قد يكون حجم الملف يتجاوز الحد المسموح (50MB).")
    else:
        await status_msg.edit_text("❌ تعذر تجاوز الحظر حالياً أو أن الفيديو محمي بموجب حقوق النشر الصارمة.")

# -------------------------------------------------------------
# 4. تشغيل البوت
# -------------------------------------------------------------
if __name__ == '__main__':
    threading.Thread(target=run_flask, daemon=True).start()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))
    print("Bot is running...")
    app.run_polling()
