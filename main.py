import os
import yt_dlp

def download_youtube_video(url, output_path="Downloads"):
    # إنشاء مجلد التنزيل إذا لم يكن موجوداً
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    # إعدادات yt-dlp للتحميل بأعلى جودة متوفرة
    ydl_opts = {
        # اختيار أعلى جودة فيديو + أعلى جودة صوت ودمجهم
        'format': 'bestvideo+bestaudio/best',
        # صيغة اسم الملف الناتج: الاسم - الجودة.الصيغة
        'outtmpl': os.path.join(output_path, '%(title)s (%(height)sp).%(ext)s'),
        # دمج الصوت والفيديو بصيغة mp4
        'merge_output_format': 'mp4',
        # السماح بتنزيل قوائم التشغيل إن وجد الرابط قائمة
        'noplaylist': False,
        # عدم التوقف في حال وجود خطأ في فيديو معين داخل القائمة
        'ignoreerrors': True,
        # إظهار نسبة التحميل بالتفصيل
        'quiet': False,
    }

    try:
        print(f"جاري بدء التحميل من: {url}")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        print("\n تم التحميل بنجاح!")
    except Exception as e:
        print(f"\n حدث خطأ أثناء التحميل: {e}")

# ================================
# تجربة التشغيل
# ================================
if __name__ == "__main__":
    # ضع رابط الفيديو أو قائمة التشغيل هنا
    video_url = input("أدخل رابط فيديو اليوتيوب: ").strip()
    if video_url:
        download_youtube_video(video_url)
    else:
        print("الرابط غير صالح!")
