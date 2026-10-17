#import required libraries 
import os
import requests
import pandas as pd
from dotenv import load_dotenv

# Load API key from the project root .env file
BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

load_dotenv(os.path.join(BASE_DIR, ".env"))

api_key = os.getenv("YOUTUBE_API_KEY")



# create data folder if not exists 
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

# YouTube API endpoints
#Collect video Ids , and channel Id
playlist_api = "https://www.googleapis.com/youtube/v3/playlistItems"
#
video_api = "https://www.googleapis.com/youtube/v3/videos"

# playlist IDs
PLAYLIST_IDS = [
    "PLblh5JKOoLUICTaGLRoHQDuF_7q2GfuJF",
    "PLZoTAELRMXVPBTrWtJkn3wWQxZkmTXGwe",
    "PLsyeobzWxl7pe_IiTfNyr55kwJPWbgxB5"

]

videos = []

# Collect all video entries from every playlist
for playlist_id in PLAYLIST_IDS:
    #For one request we retrive 50 videos
    page_token = None

    while True:
        params = {
            "key": api_key,
            "playlistId": playlist_id,
            "part": "snippet",
            "maxResults": 50
        }

        if page_token:
            params["pageToken"] = page_token

        response = requests.get(playlist_api, params=params, timeout=30)
        #if youtube return any exception it will raise here
        response.raise_for_status()

        data = response.json()

        if "error" in data:
            raise RuntimeError(data["error"])

        #The response data consists of items - key and list of map as their value
        for item in data.get("items", []):
            snippet = item.get("snippet", {})
            video_id = snippet.get("resourceId", {}).get("videoId")
            channel_id = snippet.get("channelId", "")
            channel_title = snippet.get("channelTitle","")

            if video_id:
                videos.append({
                    "id": video_id,
                    "playlist_id": playlist_id,
                    "channel_id": channel_id,
                    "channel_title": channel_title,
                    "channel_url": (
                        f"https://www.youtube.com/channel/{channel_id}"
                        if channel_id else ""
                    )
                })

        page_token = data.get("nextPageToken")

        if not page_token:
            break

    print(f"Finished playlist: {playlist_id}")

if not videos:
    raise RuntimeError("No videos were found in the playlists.")

# Get unique video IDs
video_ids = list(dict.fromkeys(v["id"] for v in videos))
video_data = []

# Fetch detailed information in batches of 50
for i in range(0, len(video_ids), 50):
    batch_ids = video_ids[i:i + 50]

    params = {
        "key": api_key,
        "id": ",".join(batch_ids),
        "part": "snippet,contentDetails,statistics"
    }

    response = requests.get(
        video_api, params=params, timeout=30
    )
    response.raise_for_status()
    data = response.json()

    if "error" in data:
        raise RuntimeError(data["error"])

    for item in data.get("items", []):
        snippet = item.get("snippet", {})
        content = item.get("contentDetails", {})
        stats = item.get("statistics", {})
        video_id = item["id"]

        video_data.append({
            "id": video_id,
            "title": snippet.get("title", ""),
            "description": snippet.get("description", ""),
            "publishedAt": snippet.get("publishedAt", ""),
            "duration": content.get("duration", ""),
            "viewCount": stats.get("viewCount"),
            "likeCount": stats.get("likeCount"),
            "url": f"https://www.youtube.com/watch?v={video_id}"
        })

    print(
        f"Fetched details for "
        f"{min(i + 50, len(video_ids))}/{len(video_ids)} videos"
    )

# Combine playlist and video information
playlist_df = pd.DataFrame(videos)
video_df = pd.DataFrame(video_data)

df = playlist_df.merge(video_df, on="id", how="left")

#  Save into  excel file 
output_path = os.path.join(DATA_DIR, "videos.xlsx")
df.to_excel(output_path, index=False)

# Display summary
print("\nData collection completed!")
print("Playlist entries:", len(df))
print("Unique videos found:", df["id"].nunique())
print("Videos with detailed metadata:", df["title"].notna().sum())
print("Excel saved to:", output_path)
