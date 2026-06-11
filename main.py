from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx

app = FastAPI(title="BiliDouyin Anti-Block Scraper Engine")

# CORS পলিসি ওপেন করা
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ওপেন সোর্স ফ্রি গ্লোবাল স্ক্রাপার গেটওয়ে (যা আইপি ব্লক বাইপাস করে)
COBALT_API = "https://api.cobalt.tools/api/json"

@app.get("/")
def home():
    return {"message": "BiliDouyin Scraper Engine is Running Live!"}

@app.get("/api/scrape")
async def scrape_video(url: str):
    if not url:
        raise HTTPException(status_code=400, detail="URL parameter is required")
    
    # প্ল্যাটফর্ম ডিটেক্ট করা
    platform = "unknown"
    if "youtube.com" in url or "youtu.be" in url:
        platform = "youtube"
    elif "douyin.com" in url:
        platform = "douyin"
    elif "bilibili.com" in url or "b23.tv" in url:
        platform = "bilibili"

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    # কোবাল্ট গেটওয়ের জন্য পে-লোড সাজানো
    payload = {
        "url": url,
        "vQuality": "720", # রেন্ডার ফ্রি র‍্যামের জন্য বেস্ট কোয়ালিটি
        "isAudioOnly": False,
        "isNoWatermark": True # ডৌইনের ওয়াটারমার্ক অটোমেটিক রিমুভ করবে
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            # গ্লোবাল গেটওয়েতে রিকোয়েস্ট পাঠানো (Render এর আইপি হাইড থাকবে)
            response = await client.post(COBALT_API, json=payload, headers=headers)
            
            if response.status_code != 200:
                return {
                    "status": "failed",
                    "platform": platform,
                    "message": "Gateway blocked or video not found"
                }
                
            data = response.json()
            video_url = data.get("url")
            
            if not video_url:
                return {
                    "status": "failed",
                    "platform": platform,
                    "message": "Direct link extraction failed"
                }

            # ফ্রন্টএন্ড প্লেয়ারের জন্য পারফেক্ট ডাটা ফরম্যাট জেনারেট করা
            return {
                "status": "success",
                "platform": platform,
                "title": data.get("text", f"{platform.capitalize()} Video"),
                "video_url": video_url,
                "thumbnail": "",
                "creator": f"@{platform}_user"
            }

        except Exception as e:
            return {
                "status": "failed",
                "platform": platform,
                "message": str(e)
    }
