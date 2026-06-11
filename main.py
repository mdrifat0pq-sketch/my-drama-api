from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import yt_dlp
import asyncio

app = FastAPI(title="BiliDouyin Scraper Engine")

# ফ্রন্টএন্ড অ্যাপ বা ওয়েবসাইট থেকে ডাটা অ্যাক্সেস করার জন্য CORS পলিসি ওপেন করা
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# yt-dlp এর বেসিক কনফিগারেশন (কোনো ফাইল ডাউনলোড হবে না, শুধু লিংক এক্সট্রাক্ট হবে)
YDL_OPTIONS = {
    'format': 'best',
    'skip_download': True,
    'noplaylist': True,
    'quiet': True,
    'no_warnings': True,
    'concurrent_fragment_downloads': 5,
    # 'cookiefile': 'cookies.txt' # Render-এ আইপি ব্লক খেলে তোর ব্রাউজারের কুকি ফাইল এখানে দিবি
}

async def extract_video_link(url: str):
    """yt-dlp লাইব্রেরিকে এসিনক্রোনাসলি রান করার ফাংশন"""
    loop = asyncio.get_event_loop()
    try:
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            # ব্লক না হয়ে ব্যাকগ্রাউন্ডে প্রসেস রান করার জন্য loop-এর সাহায্য নেওয়া
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=False))
            
            # ডিরেক্ট ভিডিওর প্লেব্যাক ইউআরএল এবং মেটাডেটা ফিল্টার করা
            return {
                "status": "success",
                "title": info.get("title"),
                "video_url": info.get("url"), # এই লিংকটাই আমরা প্লেয়ারে চালাব
                "duration": info.get("duration"),
                "thumbnail": info.get("thumbnail"),
                "creator": info.get("uploader")
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def home():
    return {"message": "BiliDouyin Scraper Engine is Running Live!"}

@app.get("/api/scrape")
async def scrape_video(url: str):
    """
    এই এন্ডপয়েন্টে ফ্রন্টএন্ড থেকে রিকোয়েস্ট আসবে।
    উদাহরণ: http://127.0.0.1:8000/api/scrape?url=ইউটিউব_শর্টস_লিংক
    """
    if not url:
        raise HTTPException(status_code=400, detail="URL parameter is required")
        
    result = await extract_video_link(url)
    return result
