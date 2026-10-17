import sys
import os
import re
from pathlib import Path
from typing import Optional, Dict, Any, List
import requests
import feedparser

# Ensure repository root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from Commands.truth import format_truth_post, is_valid_post, fetch_trumpstruth_media_map, fetch_latest_from_rss


def test_truth_social_api():
    api_url = "https://rollcall.com/wp-json/factbase/v1/twitter"
    params = {
        "platform": "truth social",
        "sort": "date",
        "sort_order": "desc",
        "page": 1,
        "format": "json"
    }
    
    print("Fetching Truth Social posts from rollcall.com API...")
    print(f"URL: {api_url}")
    print(f"Params: {params}")
    print("-" * 60)
    
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "en,en-US;q=0.9",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36"
    }
    
    response = requests.get(api_url, params=params, headers=headers, timeout=10)
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code != 200:
        print(f"Error: Failed to fetch data. Status code: {response.status_code}")
        return
    
    data = response.json()
    
    print(f"Response type: {type(data)}")
    if isinstance(data, dict):
        print(f"Response keys: {data.keys()}")
        if "results" in data:
            posts = data["results"]
        elif "data" in data:
            posts = data["data"]
        elif "items" in data:
            posts = data["items"]
        else:
            posts = list(data.values()) if data else []
            print("Using dict values as posts")
    else:
        posts = data
    
    print(f"Total posts fetched: {len(posts)}")
    print("-" * 60)
    
    print("\nFirst 10 posts formatted output:")
    for i, item in enumerate(posts[:10]):
        formatted = format_truth_post(item)
        print(f"\n[{i+1}] {formatted}")
    
    print("\n" + "=" * 60)
    print("FIRST VALID POST (latest):")
    print("=" * 60)
    
    valid_item = None
    for item in posts:
        if is_valid_post(item):
            valid_item = item
            break
        
    if valid_item:
        print(f"\nDate: {valid_item.get('date', 'N/A')}")
        print(f"Post URL: {valid_item.get('post_url', 'N/A')}")
        print(f"\nFormatted Message (Rollcall only):\n{format_truth_post(valid_item)}")
        
        # Test enrichment
        import re
        post_id = str(valid_item.get("id") or "")
        if not post_id and valid_item.get("post_url"):
            match = re.search(r"/(\d+)$", valid_item["post_url"])
            if match:
                post_id = match.group(1)
        trump_media = fetch_trumpstruth_media_map()
        enriched_item = dict(valid_item)
        if post_id and post_id in trump_media:
            post_media = trump_media[post_id]
            if post_media.get("videos"):
                enriched_item["video_url"] = post_media["videos"][0]
            if post_media.get("images"):
                enriched_item["image_url"] = post_media["images"][0]
            print(f"\nEnriched with trumpstruth.org media: {post_media}")
        else:
            print(f"\nPost {post_id} not in trumpstruth.org top posts, kept rollcall fallback.")

        print(f"\nFormatted Message (With Enrichment/Fallback):\n{format_truth_post(enriched_item)}")
    else:
        print("No valid posts found!")


def get_latest_trumpstruth_feed_media(feed_url: str = "https://www.trumpstruth.org/feed") -> Optional[Dict[str, Any]]:
    """
    Parses https://www.trumpstruth.org/feed and finds the latest entry containing media.
    """
    media_map = fetch_trumpstruth_media_map(feed_url=feed_url)
    if not media_map:
        return None

    # Find first entry that has either images or videos
    for pid, data in media_map.items():
        if data.get("images") or data.get("videos"):
            return {
                "post_id": pid,
                "images": data.get("images", []),
                "videos": data.get("videos", []),
            }

    return None


def test_feedparser_trumpstruth_feed():
    print("\n" + "=" * 60)
    print("TESTING TRUMPSTRUTH.ORG RSS FEEDPARSER:")
    print("=" * 60)
    try:
        media_map = fetch_trumpstruth_media_map()
        print(f"Total posts indexed from feed: {len(media_map)}")
        latest_media = get_latest_trumpstruth_feed_media()
        if latest_media:
            print(f"\nLatest Post with Media (ID: {latest_media['post_id']}):")
            print(f"  Images: {latest_media['images']}")
            print(f"  Videos: {latest_media['videos']}")

        print("\nSample of top 5 posts from feed:")
        sample_entries = list(media_map.items())[:5]
        for pid, data in sample_entries:
            print(f"  Post ID: {pid} | Images: {len(data['images'])} | Videos: {len(data['videos'])}")

        print("\nTesting fetch_latest_from_rss() fallback:")
        rss_fallback_item = fetch_latest_from_rss()
        if rss_fallback_item:
            print("Successfully extracted fallback item from RSS:")
            print(f"  Post ID: {rss_fallback_item['id']}")
            print(f"  Post URL: {rss_fallback_item['post_url']}")
            print(f"  Formatted Output: {format_truth_post(rss_fallback_item)}")
        else:
            print("Failed to get fallback item from RSS.")
    except Exception as e:
        print(f"Error testing feedparser: {e}")


if __name__ == "__main__":
    test_truth_social_api()
    test_feedparser_trumpstruth_feed()
