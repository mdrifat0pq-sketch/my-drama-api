from flask import Flask
import threading
import bot

app = Flask(__name__)

@app.route('/')
def home():
    return "CartSpy Bot is Alive and Running 24/7!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

if __name__ == "__main__":
    # ব্যাকগ্রাউন্ডে ফ্ল্যাস্ক সার্ভার চালু করা রেন্ডারের পোর্ট সচল রাখার জন্য
    t = threading.Thread(target=run_flask)
    t.start()
    
    # মেইন টেলিগ্রাম বট চালু করা
    bot.main()
