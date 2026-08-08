import os
import threading
import requests
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

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
# 3. دالة استخراج روابط التحميل عبر واجهات متعددة
# -------------------------------------------------------------
def get_download_link(youtube_url):
    """تجربة أكثر من API وسيط لضمان استخراج رابط التحميل"""
    apis = [
        f"https://api.vkrdown.com/v4/youtube?url={youtube_url}",
        f"https://api.cobalt.tools/api/json"
    ]
    
    # محاولة API الأول
    try:
        res = requests.get(apis[0], timeout=10).json()
        if "data" in res and "downloads" in res["data"]:
            for item in res["data"]["downloads"]:
                if item.get("extension") == "mp4" and item.get("url"):
                    return item["url"]
    except Exception:
        pass

    # محاولة API الثاني (Cobalt)
    try:
        payload = {"url": youtube_url, "videoQuality": "360"}
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        res = requests.post(apis[1], json=payload, headers=headers, timeout=10).json()
        if res.get("url"):
            return res.get("url")
    except Exception:
        pass

    return None

# -------------------------------------------------------------
# 4. أوامر ودوال البوت
# -------------------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 أهلاً بك!\n"
        "أرسل لي رابط أي فيديو من يوتيوب وسأقوم بتحميله أو إرسال رابط تحميله المباشر فوراً."
    )

async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    
    if not url.startswith("http://") and not url.startswith("https://"):
        await update.message.reply_text("❌ الرجاء إرسال رابط صحيح يبدأ بـ http أو https.")
        return

    status_msg = await update.message.reply_text("⏳ جاري معالجة الفيديو وتجاوز الحظر...")
    filename = "downloaded_video.mp4"

    # جلب رابط التحميل المباشر
    direct_link = get_download_link(url)

    if not direct_link:
        # إذا تعذر الاستخراج المباشر، إعطاء رابط بديل جاهز
        clean_url = url.replace("https://www.youtube.com/", "https://www.ssyoutube.com/")
        clean_url = clean_url.replace("https://youtu.be/", "https://www.ssyoutube.com/")
        await status_msg.edit_text(
            f"⚠️ **تعذر التنزيل المباشر بسبب حظر يوتيوب المعتاد.**\n\n"
            f"📥 **يمكنك تحميل الفيديو بنقرة واحدة من هنا:**\n{clean_url}",
            parse_mode="Markdown",
            disable_web_page_preview=False
        )
        return

    try:
        # محاولة تنزيل الفيديو ورفعه
        video_res = requests.get(direct_link, stream=True, timeout=30)
        with open(filename, 'wb') as f:
            for chunk in video_res.iter_content(chunk_size=1024*1024):
                if chunk:
                    f.write(chunk)

        file_size_mb = os.path.getsize(filename) / (1024 * 1024)

        # إذا كان الحجم ضمن المسموح في تليجرام (أقل من 50MB)
        if file_size_mb <= 49 and file_size_mb > 0:
            await status_msg.edit_text("⬆️ جاري رفع الفيديو إلى تليجرام...")
            with open(filename, 'rb') as video:
                await update.message.reply_video(video)
            os.remove(filename)
            await status_msg.delete()
        else:
            # إذا كان الفيديو كبيراً جداً، إرسال رابط التحميل المباشر فوراً
            if os.path.exists(filename):
                os.remove(filename)
            await status_msg.edit_text(
                f"🎬 **الفيديو جاهز!**\n"
                f"حجم الفيديو كبير لرفعه على تليجرام مباشرة.\n\n"
                f"📥 [اضغط هنا لتحميل الفيديو مباشرة]({direct_link})",
                parse_mode="Markdown"
            )

    except Exception:
        if os.path.exists(filename):
            try:
                os.remove(filename)
            except Exception:
                pass
        
        # في حال حدوث أي خطأ في السيرفر أثناء الرفع
        await status_msg.edit_text(
            f"📥 **رابط التحميل المباشر للفيديو:**\n{direct_link}",
            disable_web_page_preview=True
        )

# -------------------------------------------------------------
# 5. تشغيل البوت
# -------------------------------------------------------------
if __name__ == '__main__':
    threading.Thread(target=run_flask, daemon=True).start()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))
    print("Bot is active...")
    app.run_polling()
