from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from TikTokApi import TikTokApi
import asyncio
import os
from dotenv import load_dotenv
from typing import Optional, List
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

app = FastAPI(
    title="TikTok Scraper API",
    description="API for scraping TikTok data",
    version="1.0.0"
)

class TikTokRequest(BaseModel):
    username: str
    count: int = 10

class HashtagRequest(BaseModel):
    hashtag: str
    count: int = 10
    days: int = 7  # Default to last 7 days

class CountryTrendRequest(BaseModel):
    country_code: str = "US"  # Default to US
    count: int = 10
    days: int = 7  # Default to last 7 days

@app.get("/")
async def root():
    return {"message": "Welcome to TikTok Scraper API"}

@app.post("/scrape/user")
async def scrape_user_videos(request: TikTokRequest):
    try:
        # Initialize TikTok API
        async with TikTokApi() as api:
            # Get user data
            user = await api.user(username=request.username).info()
            
            # Get user videos
            videos = []
            async for video in api.user(username=request.username).videos(count=request.count):
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
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/trending/hashtag")
async def get_hashtag_trends(request: HashtagRequest):
    try:
        async with TikTokApi() as api:
            hashtag = request.hashtag.strip('#')
            videos = []
            
            # Calculate date threshold
            date_threshold = datetime.now() - timedelta(days=request.days)
            
            async for video in api.hashtag(name=hashtag).videos(count=request.count):
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
            
            return {
                "hashtag": hashtag,
                "days_filter": request.days,
                "videos": videos
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/trending/country")
async def get_country_trends(request: CountryTrendRequest):
    try:
        async with TikTokApi() as api:
            videos = []
            
            # Calculate date threshold
            date_threshold = datetime.now() - timedelta(days=request.days)
            
            async for video in api.trending.videos(count=request.count, region=request.country_code):
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
            
            return {
                "country_code": request.country_code,
                "days_filter": request.days,
                "videos": videos
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 