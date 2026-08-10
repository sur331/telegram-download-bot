import os
import yt_dlp
import telebot

# ضع توكن البوت الخاص بك من BotFather بين التنصيص
BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"

bot = telebot.TeleBot(8859717725:AAFt9FWRA5kkmzZSNsUjQ1qv79l9kSR4i4Q)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "أهلاً بك! أرسل لي رابط فيديو من يوتيوب لتحميله مباشرة.")

@bot.message_handler(func=lambda message: True)
def process_video_link(message):
    url = message.text.strip()
    
    # التحقق المبدئي من الرابط
    if not (url.startswith("http://") or url.startswith("https://")):
        bot.reply_to(message, "الرابط غير صالح! يرجى إرسال رابط يوتيوب صحيح.")
        return

    output_path = "Downloads"
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    status_msg = bot.reply_to(message, "⏳ جاري تحميل الفيديو...")

    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
        'merge_output_format': 'mp4',
        'quiet': True,
        'noplaylist': True,
        'ignoreerrors': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            # ضمان امتداد mp4 بعد الدمج
            filename = os.path.splitext(filename)[0] + ".mp4"

        bot.edit_message_text("📤 جاري إرسال الفيديو إلى تليجرام...", chat_id=status_msg.chat.id, message_id=status_msg.message_id)
        
        with open(filename, 'rb') as video_file:
            bot.send_video(message.chat.id, video_file)

        # تنظيف الملفات السيرفرية بعد الإرسال
        if os.path.exists(filename):
            os.remove(filename)
            
        bot.delete_message(chat_id=status_msg.chat.id, message_id=status_msg.message_id)

    except Exception as e:
        bot.edit_message_text(f"❌ حدث خطأ أثناء التحميل: {str(e)}", chat_id=status_msg.chat.id, message_id=status_msg.message_id)

if __name__ == '__main__':
    print("🤖 البوت يعمل الآن...")
    bot.infinity_polling()
