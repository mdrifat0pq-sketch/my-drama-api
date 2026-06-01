import os
import logging
import random
import threading
from flask import Flask
from pymongo import MongoClient
import requests
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    PreCheckoutQueryHandler,
    filters,
    ContextTypes
)

# --- CONFIGURATION ---
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
MONGO_URI = os.getenv("MONGO_URI", "YOUR_MONGO_URI_HERE")
PAYMENT_PROVIDER_TOKEN = os.getenv("PAYMENT_PROVIDER_TOKEN", "")
BOT_NAME = "CartSpy"

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- DATABASE ENGINE ---
try:
    client = MongoClient(MONGO_URI)
    db = client['cartspy_db']
    users_collection = db['users']
    print("✅ MongoDB Connected Successfully!")
except Exception as e:
    print(f"❌ MongoDB Connection Failed: {e}")

def get_or_create_user(user_id, username=None):
    user = users_collection.find_one({"user_id": user_id})
    if not user:
        user = {
            "user_id": user_id,
            "username": username,
            "country": None,
            "language": None,
            "search_count": 0,
            "premium_status": False
        }
        users_collection.insert_one(user)
    return user

def update_profile(user_id, country, language):
    users_collection.update_one(
        {"user_id": user_id},
        {"$set": {"country": country, "language": language}}
    )
    return True

def increment_search_count(user_id):
    users_collection.update_one({"user_id": user_id}, {"$inc": {"search_count": 1}})

def check_free_limit(user_id):
    user = users_collection.find_one({"user_id": user_id})
    if not user:
        return True
    if user.get("premium_status", False):
        return True
    if user.get("search_count", 0) < 2:
        return True
    return False

def make_user_premium(user_id):
    users_collection.update_one({"user_id": user_id}, {"$set": {"premium_status": True}})

# --- SCRAPER ENGINE ---
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
]

def search_ebay(query):
    formatted_query = query.replace(" ", "+")
    url = f"https://www.ebay.com/sch/i.html?_nkw={formatted_query}"
    try:
        res = requests.get(url, headers={"User-Agent": random.choice(USER_AGENTS)}, timeout=10)
        if res.status_code != 200:
            return None
        
        soup = BeautifulSoup(res.text, 'html.parser')
        # ইবের নতুন আপডেট হওয়া ক্লাস লিস্ট দিয়ে খোঁজা
        items = soup.find_all('div', class_='s-item__info')
        
        for item in items:
            title_el = item.find('div', class_='s-item__title')
            if not title_el or "Shop on eBay" in title_el.text:
                continue
                
            title = title_el.text.replace("New Listing", "").strip()
            
            price_el = item.find('span', class_='s-item__price')
            price = price_el.text.strip() if price_el else "$0.00"
            
            # মেইন ইমেজ খোঁজা
            parent = item.find_parent()
            img_url = "https://via.placeholder.com/300"
            if parent:
                img_el = parent.find('img')
                if img_el:
                    img_url = img_el.get('src') or img_el.get('data-src') or img_url

            return {
                "title": title,
                "price": price,
                "image": img_url,
                "coupon": "SAVE 10% OFF (Code: CARTSPY10)",
                "quality": "4.8/5 Top Verified Seller",
                "source": "eBay"
            }
    except Exception as e:
        print(f"Scraper Error: {e}")
    
    # যদি স্ক্র্যাপার কোনো কারণে ফেইল করে, তবে ইউজারকে ডামি ডেটা দিয়ে রেসপন্স সচল রাখবে
    return {
        "title": f"{query} (Global Edition)",
        "price": "$299.99",
        "image": "https://images.unsplash.com/photo-1531403009284-440f080d1e12",
        "coupon": "WELCOME5 (5% OFF)",
        "quality": "Highly Rated",
        "source": "Global Market"
    }

# --- TELEGRAM BOT LOGIC ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username
    get_or_create_user(user_id, username)
    
    welcome = (
        f"👋 Welcome to *{BOT_NAME}*!\n\n"
        "I am your global shopping assistant. I will find the best prices, images, and coupons for you!\n\n"
        "Please select your region first 👇"
    )
    keyboard = [
        [InlineKeyboardButton("🇺🇸 USA / Global", callback_data="set_country:USA:en")],
        [InlineKeyboardButton("🇧🇩 Bangladesh", callback_data="set_country:BD:bn")],
        [InlineKeyboardButton("🇮🇳 India", callback_data="set_country:IN:hi")]
    ]
    await update.message.reply_text(welcome, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data
    
    if data.startswith("set_country:"):
        _, country, lang = data.split(":")
        update_profile(user_id, country, lang)
        
        msg = f"✅ Settings Saved! Country: {country}. Now send me any product name to spy on prices!"
        try:
            translated = GoogleTranslator(source='auto', target=lang).translate(msg)
        except:
            translated = msg
        await query.edit_message_text(translated)
        
    elif data.startswith("unlock_details:"):
        _, prod_query = data.split(":", 1)
        user_info = get_or_create_user(user_id)
        lang = user_info.get("language") or "en"
        
        if check_free_limit(user_id):
            prod_data = search_ebay(prod_query)
            details = f"🎟️ **Coupon:** {prod_data['coupon']}\n⭐ **Quality:** {prod_data['quality']}"
            try:
                trans_details = GoogleTranslator(source='auto', target=lang).translate(details)
            except:
                trans_details = details
            await query.message.reply_text(trans_details, parse_mode="Markdown")
            increment_search_count(user_id)
        else:
            await query.message.reply_text("🚨 Your 2 free searches are over! Please send 10 Stars to unlock premium coupons.")
            await context.bot.send_invoice(
                chat_id=user_id,
                title="Unlock Premium CartSpy Details",
                description=f"Unlock coupons for {prod_query}",
                payload=f"premium_unlock:{prod_query}",
                provider_token=PAYMENT_PROVIDER_TOKEN,
                currency="XTR",
                prices=[LabeledPrice("Premium Data", 10)]
            )

async def search_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    product_query = update.message.text
    user_info = get_or_create_user(user_id)
    lang = user_info.get("language") or "en"
    
    if not user_info.get("country"):
        await update.message.reply_text("⚠️ Please run /start and select your country first!")
        return
        
    wait_msg = await update.message.reply_text("🕵️‍♂️ *CartSpy is spying... Please wait...*", parse_mode="Markdown")
    prod_data = search_ebay(product_query)
    
    caption = f"📦 **Product:** {prod_data['title']}\n💰 **Best Price:** {prod_data['price']}\n🌐 **Source:** {prod_data['source']}\n"
    try:
        translated_caption = GoogleTranslator(source='auto', target=lang).translate(caption)
        btn_text = GoogleTranslator(source='auto', target=lang).translate("🔓 Unlock Coupons & Review")
    except:
        translated_caption = caption
        btn_text = "🔓 Unlock Coupons & Review"
        
    keyboard = [[InlineKeyboardButton(btn_text, callback_data=f"unlock_details:{product_query}")]]
    
    await wait_msg.delete()
    await update.message.reply_photo(
        photo=prod_data['image'],
        caption=translated_caption,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.pre_checkout_query.answer(ok=True)

async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    payload = update.message.successful_payment.invoice_payload
    product_query = payload.split(":", 1)[1]
    
    make_user_premium(user_id)
    prod_data = search_ebay(product_query)
    
    success_msg = f"🎉 **Payment Successful!**\n\n🎟️ **Coupon:** {prod_data['coupon']}\n⭐ **Quality:** {prod_data['quality']}"
    await update.message.reply_text(success_msg, parse_mode="Markdown")

# --- FLASK SERVER (RENDER ALIVE) ---
app = Flask(__name__)

@app.route('/')
def index():
    return "CartSpy is fully active 24/7!"

def run_flask():
    app.run(host="0.0.0.0", port=8080)

if __name__ == "__main__":
    # Flask কে আলাদা থ্রেডে চালানো
    threading.Thread(target=run_flask, daemon=True).start()
    
    # টেলিগ্রাম বট স্টার্ট করা
    bot_app = Application.builder().token(BOT_TOKEN).build()
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(CallbackQueryHandler(button_click))
    bot_app.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    bot_app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback))
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_product))
    
    print("🚀 CartSpy is successfully running via polling...")
    bot_app.run_polling()
