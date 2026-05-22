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
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    
    # ১. সরাসরি বটের ভেতর মিনি অ্যাপ ওপেন করার বাটন
    webapp_info = telebot.types.WebAppInfo(WEB_APP_URL)
    btn_app = telebot.types.InlineKeyboardButton(text="🎬 STREAM NOW", web_app=webapp_info)
    
    # ২. অফিশিয়াল চ্যানেল জয়েন করার বাটন
    btn_channel = telebot.types.InlineKeyboardButton(text="📢 Official Channel", url="https://t.me/flixora_official_channel")
    
    # ৩. কন্টাক্ট সাপোর্ট বাটন
    btn_contact = telebot.types.InlineKeyboardButton(text="💬 Contact Support", url="https://t.me/mdrifat021u")
    
    # সবগুলো বাটন নিচে নিচে (row_width=1) সাজানো হলো
    markup.add(btn_app, btn_channel, btn_contact)
    
    # নতুন এবং আপডেটেড ওয়েলকাম মেসেজ টেক্সট (তোর দেওয়া টেক্সটের সাথে নতুন ইনফো ও হরর ফন্ট যুক্ত)
    welcome_text = (
        "👋 𝕎𝕖𝕝𝕔𝕠𝕞𝕖 𝕥𝕠 𝔽𝕝𝕚𝕩𝕠𝕣𝕒 | ℙref联𝕦𝕞 𝕊𝕥𝕣𝕖𝕒𝕞 🎬\n\n"
        "✨ 𝘠𝘰𝘶𝘳 𝘜𝘭𝘵𝘪𝘮𝘢𝘵ε 𝘌𝘯𝘵ε𝘳𝘵𝘢𝘪𝘯𝕞ε𝘯𝘵 𝘏🇺𝘣 𝘪𝘴 𝘏ε𝘳ε! 🍿\n"
        "Explore the best collection of Asian entertainment, 100% Free with NO premium subscription required!\n\n"
        "🇬🇧 🌟 Note: All movies and series are fully available with English Subtitles!\n\n"
        "🔥 𝕆𝕦𝕣 ℂ𝕒𝕥𝕖𝕘𝕠𝕣𝕚𝕖𝕤:\n"
        "🎭 🇰🇷 K-Dramas & Rom-Coms\n"
        "🇨🇳 C-Dramas & Historical Series\n"
        "👻 🇮🇩 Thrilling Indonesian Horror\n"
        "🧟‍♂️ 🇨🇳 Spine-chilling Chinese Horror\n\n"
        "📢 Join our Official Channel to get all updates & links:\n"
        "👉 https://t.me/flixora_official_channel 👈\n\n"
        "💬 For any inquiries or support, contact us directly:\n"
        "👉 @mdrifat021u 👈\n\n"
        "🚀 Enjoy ultra-fast streaming with premium 1080p quality.\n\n"
        "👇 Tap the buttons below to start watching and join us!\n\n"
        "𝔓𝔬𝔴𝔢𝔯𝔢𝔡 𝔟𝔶 ℜ𝔦𝔣𝔞𝔱"
    )
    
    # প্রথমে ইমেজ লোড হবে এবং ক্যাপশনে মেসেজ ও নিচে বাটন থাকবে
    bot.send_photo(message.chat.id, IMAGE_URL, caption=welcome_text, reply_markup=markup)

# バックグラウンドでフラスクウェブサーバーを動かす関数
def run():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

def keep_alive():
    t = Thread(target=run)
    t.start()

if __name__ == "__main__":
    keep_alive()           
    print("Bot is polling...")
    bot.infinity_polling()
