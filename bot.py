import os
import telebot
from flask import Flask
from threading import Thread

# রেন্ডারের এনভায়রনমেন্ট ভ্যারিয়েবল থেকে টোকেন লোড
BOT_TOKEN = os.environ.get("BOT_TOKEN") 
WEB_APP_URL = "https://mdrifat0pq-sketch.github.io/moviebox-/"
IMAGE_URL = "https://i.ibb.co.com/M5N4Syrj/1779382546976.png"

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask('')

# Render সার্ভার সচল রাখার জন্য ডামি হোম পেজ
@app.route('/')
def home():
    return "Flixora Bot is Running 24/7!"

# বটের /start কমান্ডের প্রিমিয়াম রেসপন্স (ইমেজ + টেক্সট + বাটন)
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = telebot.types.InlineKeyboardMarkup()
    
    # সরাসরি বটের ভেতর মিনি অ্যাপ ওপেন করার বাটন
    webapp_info = telebot.types.WebAppInfo(WEB_APP_URL)
    btn = telebot.types.InlineKeyboardButton(text="🎬 STREAM NOW", web_app=webapp_info)
    markup.add(btn)
    
    # নতুন এবং আপডেটেড ওয়েলকাম মেসেজ টেক্সট
    welcome_text = (
        "👋 𝕎𝕖𝕝𝕔𝕠𝕞𝕖 𝕥𝕠 𝔽𝕝𝕚𝕩𝕠𝕣𝕒 | ℙ𝕣𝕖𝕞联𝕦𝕞 𝕊𝕥𝕣𝕖𝕒𝕞 🎬\n\n"
        "✨ 𝘠𝘰𝘶𝘳 𝘜𝘭𝘵𝘪𝘮𝘢𝘵𝘦 𝘌𝘯𝘵𝘦𝘳𝘵𝘢𝘪𝘯𝕞𝘦𝘯𝘵 𝘏🇺𝘣 𝘪𝘴 𝘏𝘦𝘳𝘦! 🍿\n"
        "Explore the best collection of Asian entertainment, 100% Free with NO premium subscription required!\n\n"
        "🇬🇧 🌟 Note: All movies and series are fully available with English Subtitles!\n\n"
        "🔥 𝕆𝕦𝕣 ℂ𝕒𝕥𝕖𝕘𝕠𝕣𝕚𝕖𝕤:\n"
        "🎭 🇰🇷 K-Dramas & Rom-Coms\n"
        "🇨🇳 C-Dramas & Historical Series\n"
        "👻 🇮🇩 Thrilling Indonesian Horror\n"
        "🧟‍♂️ 🇨🇳 Spine-chilling Chinese Horror\n\n"
        "🚀 Enjoy ultra-fast streaming with premium 1080p quality.\n\n"
        "👇 Tap the button below to start watching instantly!"
    )
    
    # প্রথমে ইমেজ লোড হবে এবং ক্যাপশনে মেসেজ ও নিচে বাটন থাকবে
    bot.send_photo(message.chat.id, IMAGE_URL, caption=welcome_text, reply_markup=markup)

# ব্যাকগ্রাউন্ডে ফ্ল্যাস্ক ওয়েব সার্ভার রান করার ফাংশন
def run():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

def keep_alive():
    t = Thread(target=run)
    t.start()

if __name__ == "__main__":
    keep_alive()           
    print("Bot is polling...")
    bot.infinity_polling()
