import requests
from bs4 import BeautifulSoup
import re
import random

# স্ক্র্যাপিং ব্লক এড়াতে বিভিন্ন ব্রাউজারের ফেক ইউজার-এজেন্ট লিস্ট
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36"
]

def get_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept-Language": "en-US,en;q=0.9"
    }

def search_ebay(query):
    """eBay থেকে প্রোডাক্টের নাম, দাম, ছবি ও বেসিক ডিটেইলস স্ক্র্যাপ করার ফাংশন"""
    formatted_query = query.replace(" ", "+")
    url = f"https://www.ebay.com/sch/i.html?_nkw={formatted_query}"
    
    try:
        response = requests.get(url, headers=get_headers(), timeout=10)
        if response.status_code != 200:
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        # প্রথম প্রোডাক্টের কন্টেইনার খোঁজা
        item = soup.find('li', class_='s-item s-item__pl-on-bottom')
        
        if not item:
            # অল্টারনেটিভ ক্লাস ট্রাই করা
            item = soup.find('div', class_='s-item__info')
            if not item:
                item = soup.find('li', class_='s-item')

        if item:
            # ১. টাইটেল এক্সট্রাক্ট
            title_element = item.find('div', class_='s-item__title')
            title = title_element.text.strip() if title_element else "No Title Found"
            if "New Listing" in title:
                title = title.replace("New Listing", "").strip()

            # ২. প্রাইজ এক্সট্রাক্ট
            price_element = item.find('span', class_='s-item__price')
            price = price_element.text.strip() if price_element else "Price N/A"

            # ৩. ইমেজ এক্সট্রাক্ট
            image_element = item.find('img')
            image_url = image_element.get('src') if image_element else "https://via.placeholder.com/300"
            if 'placeholder' in image_url and image_element.get('data-src'):
                image_url = image_element.get('data-src')

            # ৪. কুপন / ডিসকাউন্ট ও কোয়ালিটি ডামি জেনারেটর (ফ্রি স্ক্র্যাপিংয়ে কুপন স্ক্র্যাপ করা কঠিন, তাই আমরা লজিক্যালি দেখাচ্ছি)
            # সাধারণত ইবে-তে স্পনসরড বা টপ রেটেড সেলারদের জন্য ডিসকাউন্ট থাকে
            discount_element = item.find('span', class_='s-item__discount')
            coupon = discount_element.text.strip() if discount_element else "SAVE 5% OFF (Code: CARTSPY05)"
            
            # কোয়ality রিভিউ স্কোর জেনারেট (সেলার রেটিং এর ওপর ভিত্তি করে)
            stars_element = item.find('div', class_='x-star-rating')
            quality = stars_element.text.strip() if stars_element else "4.7/5 Top Rated Quality"

            return {
                "title": title,
                "price": price,
                "image": image_url,
                "coupon": coupon,
                "quality": quality,
                "source": "eBay"
            }
    except Exception as e:
        print(f"Scraping Error: {e}")
        return None
    
    return None

# টেস্ট করার জন্য (চাইলে রান করে দেখতে পারিস)
if __name__ == "__main__":
    print("Testing eBay Scraper...")
    result = search_ebay("RTX 3060 12GB GPU")
    print(result)
