from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from TikTokApi import TikTokApi
import asyncio
import os
from dotenv import load_dotenv
from typing import Optional, List
from datetime import datetime, timedelta
import nest_asyncio
import random
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Apply nest_asyncio to fix event loop issues
nest_asyncio.apply()

# Load environment variables
load_dotenv()

# List of common user agents
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
]

app = FastAPI(
    title="TikTok Scraper API",
    description="API for scraping TikTok data",
    version="1.0.0"
)

class TikTokRequest(BaseModel):
    username: str
    count: int = 10
    use_proxy: bool = False
    proxy: Optional[str] = None

class HashtagRequest(BaseModel):
    hashtag: str
    count: int = 10
    days: int = 7
    use_proxy: bool = False
    proxy: Optional[str] = None

class CountryTrendRequest(BaseModel):
    country_code: str = "US"
    count: int = 10
    days: int = 7
    use_proxy: bool = False
    proxy: Optional[str] = None

def get_api_instance(use_proxy: bool = False, proxy: Optional[str] = None):
    """Create a TikTokApi instance with optional proxy"""
    logger.info("Creating TikTokApi instance")
    
    # Get all necessary cookies
    device_id = os.getenv("TIKTOK_DEVICE_ID", "")
    verify_fp = os.getenv("TIKTOK_VERIFY_FP", "")
    session_id = os.getenv("TIKTOK_SESSION_ID", "")
    
    # Create full cookie string
    cookie_str = (
        f"sessionid={session_id}; "
        f"ttwid={device_id}; "
        f"s_v_web_id={verify_fp}; "
        f"tt_webid={device_id}; "
        f"tt_webid_v2={device_id}"
    )
    
    # Configure options
    options = {
        "custom_device_id": device_id,
        "use_test_endpoints": False,  # Changed to False to use production endpoints
        "custom_verify_fp": verify_fp,
        "custom_session_id": session_id,
        "headers": {
            "User-Agent": random.choice(USER_AGENTS),
            "Cookie": cookie_str,
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Referer": "https://www.tiktok.com/",
            "Origin": "https://www.tiktok.com"
        }
    }
    
    if use_proxy and proxy:
        logger.info(f"Using proxy: {proxy}")
        options["proxies"] = {
            "http": proxy,
            "https": proxy
        }
    
    logger.info("API options configured")
    return TikTokApi(**options)

@app.get("/")
async def root():
    return {"message": "Welcome to TikTok Scraper API"}

@app.post("/scrape/user")
async def scrape_user_videos(request: TikTokRequest):
    try:
        logger.info(f"Attempting to scrape videos for user: {request.username}")
        api = get_api_instance(request.use_proxy, request.proxy)
        
        # Get user data
        logger.info("Fetching user info")
        user = await api.user(username=request.username).info()
        logger.info(f"User info fetched successfully for: {user.username}")
        
        # Get user videos
        videos = []
        logger.info(f"Fetching {request.count} videos")
        user_videos = await api.user(username=request.username).videos(count=request.count)
        
        for video in user_videos:
            video_data = {
                "id": video.id,
                "desc": video.desc,
                "create_time": video.create_time,
                "author": {
                    "username": video.author.username,
                    "nickname": video.author.nickname,
                },
                "stats": {
                    "play_count": video.stats.play_count,
                    "digg_count": video.stats.digg_count,
                    "comment_count": video.stats.comment_count,
                    "share_count": video.stats.share_count,
                },
                "video_url": video.video.download_addr,
            }
            videos.append(video_data)
        
        logger.info(f"Successfully fetched {len(videos)} videos")
        await api.close()
        return {
            "user_info": {
                "username": user.username,
                "nickname": user.nickname,
                "follower_count": user.stats.follower_count,
                "following_count": user.stats.following_count,
                "likes_count": user.stats.likes_count,
            },
            "videos": videos
        }
    except Exception as e:
        logger.error(f"Error in scrape_user_videos: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/trending/hashtag")
async def get_hashtag_trends(request: HashtagRequest):
    try:
        logger.info(f"Fetching trends for hashtag: {request.hashtag}")
        api = get_api_instance(request.use_proxy, request.proxy)
        hashtag = request.hashtag.strip('#')
        videos = []
        
        # Calculate date threshold
        date_threshold = datetime.now() - timedelta(days=request.days)
        
        # Get hashtag videos
        logger.info(f"Requesting {request.count} videos")
        hashtag_videos = await api.hashtag(name=hashtag).videos(count=request.count)
        
        for video in hashtag_videos:
            # Convert create_time to datetime
            video_date = datetime.fromtimestamp(video.create_time)
            
            # Skip videos older than the threshold
            if video_date < date_threshold:
                continue
            
            video_data = {
                "id": video.id,
                "desc": video.desc,
                "create_time": video.create_time,
                "create_date": video_date.isoformat(),
                "author": {
                    "username": video.author.username,
                    "nickname": video.author.nickname,
                },
                "stats": {
                    "play_count": video.stats.play_count,
                    "digg_count": video.stats.digg_count,
                    "comment_count": video.stats.comment_count,
                    "share_count": video.stats.share_count,
                },
                "hashtags": [tag.name for tag in video.challenges],
                "video_url": video.video.download_addr,
            }
            videos.append(video_data)
        
        logger.info(f"Successfully fetched {len(videos)} videos")
        await api.close()
        return {
            "hashtag": hashtag,
            "days_filter": request.days,
            "videos": videos
        }
    except Exception as e:
        logger.error(f"Error in get_hashtag_trends: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/trending/country")
async def get_country_trends(request: CountryTrendRequest):
    try:
        logger.info(f"Fetching trends for country: {request.country_code}")
        api = get_api_instance(request.use_proxy, request.proxy)
        videos = []
        
        # Calculate date threshold
        date_threshold = datetime.now() - timedelta(days=request.days)
        
        # Get trending videos
        logger.info(f"Requesting {request.count} videos")
        trending_videos = await api.trending.videos(count=request.count, region=request.country_code)
        
        for video in trending_videos:
            # Convert create_time to datetime
            video_date = datetime.fromtimestamp(video.create_time)
            
            # Skip videos older than the threshold
            if video_date < date_threshold:
                continue
            
            video_data = {
                "id": video.id,
                "desc": video.desc,
                "create_time": video.create_time,
                "create_date": video_date.isoformat(),
                "author": {
                    "username": video.author.username,
                    "nickname": video.author.nickname,
                },
                "stats": {
                    "play_count": video.stats.play_count,
                    "digg_count": video.stats.digg_count,
                    "comment_count": video.stats.comment_count,
                    "share_count": video.stats.share_count,
                },
                "hashtags": [tag.name for tag in video.challenges],
                "video_url": video.video.download_addr,
            }
            videos.append(video_data)
        
        logger.info(f"Successfully fetched {len(videos)} videos")
        await api.close()
        return {
            "country_code": request.country_code,
            "days_filter": request.days,
            "videos": videos
        }
    except Exception as e:
        logger.error(f"Error in get_country_trends: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 