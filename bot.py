import logging
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
from deep_translator import GoogleTranslator

import config
import database
import scraper

# লগিং সেটআপ (যাতে কোনো এরর হলে টার্মিনালে দেখা যায়)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """নতুন ইউজারকে স্বাগত জানানো এবং দেশ/ভাষা সিলেক্ট করার বাটন দেওয়া"""
    user_id = update.effective_user.id
    username = update.effective_user.username
    
    # ডেটাবেসে ইউজার তৈরি বা চেক করা
    database.get_or_create_user(user_id, username)
    
    welcome_text = (
        f"👋 Welcome to *{config.BOT_NAME}*!\n\n"
        "I am your global shopping assistant. I scan top e-commerce platforms "
        "to find the best prices, images, and exclusive coupons based on your location!\n\n"
        "Please select your region first 👇"
    )
    
    # দেশ সিলেক্ট করার বাটন (গ্লোবাল ইউজারদের জন্য)
    keyboard = [
        [InlineKeyboardButton("🇺🇸 USA / Global", callback_data="set_country:USA:en")],
        [InlineKeyboardButton("🇬🇧 United Kingdom", callback_data="set_country:UK:en")],
        [InlineKeyboardButton("🇧🇩 Bangladesh", callback_data="set_country:BD:bn")],
        [InlineKeyboardButton("🇮🇳 India", callback_data="set_country:IN:hi")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_text, parse_mode="Markdown", reply_markup=reply_markup)

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ইউজারের বাটন ক্লিকের রেসপন্স হ্যান্ডেল করা"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = query.from_user.id
    
    # দেশ ও ভাষা সেট করা
    if data.startswith("set_country:"):
        _, country, lang = data.split(":")
        database.update_profile(user_id, country, lang)
        
        # ইউজারের ভাষায় কনফার্মেশন মেসেজ
        msg = f"✅ Settings Saved! Country: {country}. You can now type any product name to search!"
        translated_msg = GoogleTranslator(source='auto', target=lang).translate(msg)
        
        await query.edit_message_text(translated_msg)
        
    # প্রিমিয়াম ডিটেইলস (কুপন ও রিভিউ) বাটন ক্লিক করলে
    elif data.startswith("unlock_details:"):
        _, product_query = data.split(":", 1)
        
        # ৩ নম্বর সার্চ থেকে ফ্রি লিমিট চেক
        if database.check_free_limit(user_id):
            # ফ্রি ট্রায়াল থাকলে সরাসরি কুপন ও কোয়ালিটি দেখিয়ে দেওয়া
            prod_data = scraper.search_ebay(product_query)
            user_info = database.get_or_create_user(user_id)
            lang = user_info.get("language") or "en"
            
            if prod_data:
                details = f"🎟️ **Coupon:** {prod_data['coupon']}\n⭐ **Quality:** {prod_data['quality']}"
                trans_details = GoogleTranslator(source='auto', target=lang).translate(details)
                await query.message.reply_text(trans_details, parse_mode="Markdown")
                database.increment_search_count(user_id)
            else:
                await query.message.reply_text("Product data lost. Please search again.")
        else:
            # ফ্রি ট্রায়াল শেষ, এবার ১০টি টেলিগ্রাম স্টারের ইনভয়েস পাঠানো হবে
            await query.message.reply_text("🚨 Your free searches are over! Send 10 Stars to unlock full details.")
            
            # Telegram Stars Invoice জেনারেট
            title = "Unlock CartSpy Premium Details"
            description = f"Get secret coupons and quality scores for: {product_query}"
            payload = f"premium_unlock:{product_query}"
            currency = "XTR"  # XTR হলো Telegram Stars এর কারেন্সি কোড
            prices = [LabeledPrice("Premium Data", 10)]  # ১০ স্টারস
            
            await context.bot.send_invoice(
                chat_id=user_id,
                title=title,
                description=description,
                payload=payload,
                provider_token=config.PAYMENT_PROVIDER_TOKEN, # স্টারের জন্য সাধারণত খালি রাখলেই চলে
                currency=currency,
                prices=prices
            )

async def search_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ইউজার প্রোডাক্টের নাম লিখে মেসেজ দিলে স্ক্র্যাপ করে রেজাল্ট পাঠানো"""
    user_id = update.effective_user.id
    product_query = update.message.text
    
    user_info = database.get_or_create_user(user_id)
    lang = user_info.get("language") or "en"
    
    # যদি ইউজার দেশ সেট না করে সরাসরি সার্চ করে
    if not user_info.get("country"):
        await update.message.reply_text("⚠️ Please run /start and select your country first!")
        return
        
    await update.message.reply_text("🕵️‍♂️ *CartSpy is spying on e-commerce sites... Please wait...*", parse_mode="Markdown")
    
    # ইবে স্ক্র্যাপার কল করা
    prod_data = scraper.search_ebay(product_query)
    
    if not prod_data:
        await update.message.reply_text("❌ Sorry, no product found! Try checking your spelling.")
        return
        
    # রেসপন্স সাজানো (নাম এবং বেসিক দাম সবার জন্য ফ্রি)
    caption_text = (
        f"📦 **Product:** {prod_data['title']}\n"
        f"💰 **Best Price:** {prod_data['price']}\n"
        f"🌐 **Source:** {prod_data['source']}\n\n"
        f"👇 Below features are locked after 2 free searches!"
    )
    
    # ইউজারের সেট করা ভাষায় অটোমেটিক অনুবাদ (Multi-language Support)
    translated_caption = GoogleTranslator(source='auto', target=lang).translate(caption_text)
    
    # বাটনের টেক্সটও ট্রান্সলেট করা
    btn_text = GoogleTranslator(source='auto', target=lang).translate("🔓 Unlock Coupons & Quality Review")
    
    keyboard = [[InlineKeyboardButton(btn_text, callback_data=f"unlock_details:{product_query}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # ইমেজসহ সুন্দর মেসেজ পাঠানো
    await update.message.reply_photo(
        photo=prod_data['image'],
        caption=translated_caption,
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """টেলিগ্রাম পেমেন্ট সাবমিট করার আগের ভ্যালিডেশন (অটো-অ্যাপ্রুভ)"""
    query = update.pre_checkout_query
    if query.invoice_payload.startswith("premium_unlock:"):
        await query.answer(ok=True)
    else:
        await query.answer(ok=False, error_message="Something went wrong.")

async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """পেমেন্ট সফল হলে এই ফাংশনটি রান হবে এবং সিক্রেট ডেটা আনলক করবে"""
    user_id = update.effective_user.id
    payload = update.message.successful_payment.invoice_payload
    product_query = payload.split(":", 1)[1]
    
    user_info = database.get_or_create_user(user_id)
    lang = user_info.get("language") or "en"
    
    # ইউজারকে ডেটাবেসে প্রিমিয়াম মেম্বার করে দেওয়া (বা সার্চ কাউন্ট রিসেট করা)
    database.make_user_premium(user_id)
    
    # এবার লক থাকা কুপন ও কোয়ালিটি ডেটা স্ক্র্যাপ করে পাঠিয়ে দেওয়া
    prod_data = scraper.search_ebay(product_query)
    if prod_data:
        success_msg = (
            "🎉 **Payment Successful! Premium Details Unlocked:**\n\n"
            f"🎟️ **Exclusive Coupon:** {prod_data['coupon']}\n"
            f"⭐ **Quality & Seller Rating:** {prod_data['quality']}"
        )
        trans_msg = GoogleTranslator(source='auto', target=lang).translate(success_msg)
        await update.message.reply_text(trans_msg, parse_mode="Markdown")
    else:
        await update.message.reply_text("Payment received, but error fetching details. Contact support.")

def main():
    """বট অ্যাপ্লিকেশন রান করা"""
    app = Application.builder().token(config.BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_click))
    app.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_product))
    
    print("CartSpy Bot is successfully running...")
    app.run_polling()

if __name__ == "__main__":
    main()
