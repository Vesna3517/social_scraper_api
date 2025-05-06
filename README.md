# TikTok Scraper API

A FastAPI-based API for scraping TikTok user data and videos.

## Setup

### Option 1: Local Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the API:
```bash
python main.py
```

### Option 2: Docker Setup

1. Build and run with Docker Compose:
```bash
docker-compose up --build
```

To run in detached mode:
```bash
docker-compose up -d
```

To stop the service:
```bash
docker-compose down
```

The API will be available at `http://localhost:8000`

## API Endpoints

### GET /
- Welcome message

### POST /scrape/user
Scrape user data and videos from TikTok

Request body:
```json
{
    "username": "tiktok_username",
    "count": 10  // optional, defaults to 10
}
```

### POST /trending/hashtag
Get trending videos for a specific hashtag

Request body:
```json
{
    "hashtag": "dance",  // without # symbol
    "count": 10,  // optional, defaults to 10
    "days": 7  // optional, defaults to 7 (last 7 days)
}
```

### POST /trending/country
Get trending videos for a specific country

Request body:
```json
{
    "country_code": "US",  // optional, defaults to "US"
    "count": 10,  // optional, defaults to 10
    "days": 7  // optional, defaults to 7 (last 7 days)
}
```

Response for trending endpoints includes:
- List of videos with details (description, stats, video URL, etc.)
- Hashtags used in each video
- Author information
- Video statistics
- Creation date in ISO format
- Number of days used for filtering

## API Documentation

Once the server is running, you can access the interactive API documentation at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Docker Configuration

The project includes Docker configuration with the following features:
- Uses Python 3.9 slim image
- Automatic restart on failure
- Health check endpoint
- Volume mounting for development
- Timezone configuration
- Port mapping (8000:8000)

## Note

This API uses the TikTokApi library which may require additional setup for authentication. Make sure to follow the TikTokApi documentation for any additional configuration needed. 