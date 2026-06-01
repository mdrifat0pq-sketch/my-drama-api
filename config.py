import os

# Telegram Bot Token (BotFather থেকে যেটা পাবি)
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# MongoDB Connection URI (MongoDB Atlas এর ফ্রি লিংক)
MONGO_URI = os.getenv("MONGO_URI", "YOUR_MONGO_URI_HERE")

# Telegram Stars পемыেন্টের জন্য Provider Token
# (টেলিগ্রাম স্টারের জন্য এটা সাধারণত খালি রাখলেও চলে অথবা "PROVIDER_TOKEN" দিতে হয়)
PAYMENT_PROVIDER_TOKEN = os.getenv("PAYMENT_PROVIDER_TOKEN", "")

# বটের নাম
BOT_NAME = "CartSpy"
