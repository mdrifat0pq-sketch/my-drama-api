from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import yt_dlp
import asyncio
import httpx
import re

app = FastAPI(title="BiliDouyin Premium Scraper Engine")

# CORS পলিসি ওপেন করা যাতে ফ্রন্টএন্ড অ্যাপ সহজে ডেটা পায়
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

YDL_OPTIONS = {
    'format': 'best',
    'skip_download': True,
    'noplaylist': True,
    'quiet': True,
    'no_warnings': True,
    'concurrent_fragment_downloads': 5
}

# --- Douyin No-Watermark Custom Engine ---
async def scrape_douyin_no_wm(url: str):
    """কোনো API কী ছাড়া ডৌইনের ওয়াটারমার্ক ছাড়া আসল .mp4 লিংক বের করার ইঞ্জিন"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Mobile Safari/537.36"
    }
    async with httpx.AsyncClient(headers=headers, follow_redirects=True) as client:
        try:
            # শর্ট বা শেয়ারড ইউআরএল থেকে আসল ভিডিও আইডি এক্সট্রাক্ট করা
            response = await client.get(url)
            real_url = str(response.url)
            
            video_id_match = re.search(f"video/(\\d+)", real_url)
            if not video_id_match:
                raise HTTPException(status_code=400, detail="Invalid Douyin URL structure")
                
            video_id = video_id_match.group(1)
            
            # Douyin অফিশিয়াল ওয়েব ব্যাকএন্ড API-তে হিট করা
            api_url = f"https://www.douyin.com/aweme/v1/web/aweme/detail/?aweme_id={video_id}"
            api_res = await client.get(api_url)
            data = api_res.json()
            
            aweme_detail = data.get("aweme_detail", {})
            video_data = aweme_detail.get("video", {})
            
            # ওয়াটারমার্ক ছাড়া ডিরেক্ট প্লেব্যাক লিংক ফিল্টার (wm লেখা রিপ্লেস করে)
            wm_video_url = video_data.get("play_addr", {}).get("url_list", [None])[0]
            if not wm_video_url:
                raise HTTPException(status_code=404, detail="Video address not found")
                
            no_wm_url = wm_video_url.replace("playwm", "play")
            
            return {
                "status": "success",
                "platform": "douyin",
                "title": aweme_detail.get("desc", "Douyin Video"),
                "video_url": no_wm_url,
                "thumbnail": video_data.get("cover", {}).get("url_list", [None])[0],
                "creator": aweme_detail.get("author", {}).get("nickname", "Unknown Creator")
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Douyin Error: {str(e)}")

# --- YouTube & Bilibili Generic Engine ---
async def extract_generic_link(url: str, platform: str):
    loop = asyncio.get_event_loop()
    try:
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=False))
            return {
                "status": "success",
                "platform": platform,
                "title": info.get("title"),
                "video_url": info.get("url"),
                "duration": info.get("duration"),
                "thumbnail": info.get("thumbnail"),
                "creator": info.get("uploader")
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{platform.capitalize()} Error: {str(e)}")

@app.get("/")
def home():
    return {"message": "BiliDouyin Scraper Engine is Running Live!"}

@app.get("/api/scrape")
async def scrape_video(url: str):
    if not url:
        raise HTTPException(status_code=400, detail="URL parameter is required")
    
    # ইউআরএল চেক করে অটোমেটিক ইঞ্জিন সিলেক্ট করা
    if "douyin.com" in url:
        return await scrape_douyin_no_wm(url)
    elif "bilibili.com" in url or "b23.tv" in url:
        return await extract_generic_link(url, "bilibili")
    elif "youtube.com" in url or "youtu.be" in url:
        return await extract_generic_link(url, "youtube")
    else:
        raise HTTPException(status_code=400, detail="Unsupported platform URL")
