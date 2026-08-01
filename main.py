import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from yt_dlp import YoutubeDL

# إعداد السجلات لتتبع أي مشاكل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# توكن البوت (يمكنك استخدامه كمتغير بيئي أو وضع التوكن الخاص بك)
BOT_TOKEN = os.getenv("BOT_TOKEN", "8859717725:AAFt9FWRA5kkmzZSNsUjQ1qv79l9kSR4i4Q")

# دالة الترحيب /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "أهلاً بك! 👋\n\nأرسل لي رابط فيديو أو ريلز (Reel) من **إنستغرام** وسأقوم بتحميله لك فوراً."
    )

# دالة تحميل محتوى إنستغرام
async def handle_instagram_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()

    # التحقق من أن الرابط يخص منصة إنستغرام
    if not ("instagram.com" in url or "instagr.am" in url):
        await update.message.reply_text("❌ الرجاء إرسال رابط صحيح من منصة إنستغرام.")
        return

    status_msg = await update.message.reply_text("جاري جلب الفيديو من إنستغرام... انتظر لحظة ⏳")

    # إنشاء مجلد لتنزيلات الفيديو المؤقتة
    if not os.path.exists('downloads'):
        os.makedirs('downloads')

    # إعدادات yt-dlp المتوافقة خصيصاً مع إنستغرام
    ydl_opts = {
        'format': 'best[ext=mp4]/best',
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        # إضافة رؤوس محاكاة المتصفح لمنع التظليل/الحظر
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
        }
    }

    downloaded_file = None

    try:
        # عملية استخراج وتحميل الفيديو
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            downloaded_file = ydl.prepare_filename(info)

        # التحقق من وجود الملف المحمل وإرساله
        if downloaded_file and os.path.exists(downloaded_file):
            with open(downloaded_file, 'rb') as video:
                await update.message.reply_video(
                    video=video,
                    caption="تم تحميل الفيديو بنجاح! 📸🎬"
                )
            
            # حذف رسالة الانتظار
            await status_msg.delete()
        else:
            await status_msg.edit_text("❌ تعذر العثور على ملف الفيديو للتحميل.")

    except Exception as e:
        logging.error(f"حدث خطأ أثناء تحميل إنستغرام: {e}")
        await status_msg.edit_text(
            "❌ حدث خطأ أثناء التحميل.\n"
            "• تأكد أن الحساب **عام (Public)** وليس خاصاً (Private).\n"
            "• تأكد من صحة الرابط."
        )

    finally:
        # التنظيف الذاتي: حذف الفيديو بعد الإرسال لتوفير مساحة السيرفر
        if downloaded_file and os.path.exists(downloaded_file):
            try:
                os.remove(downloaded_file)
            except Exception:
                pass

# التشغيل الرئيسي
if __name__ == '__main__':
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_instagram_media))

    print("البوت يعمل بنجاح الآن...")
    app.run_polling()
