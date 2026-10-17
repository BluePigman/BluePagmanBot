import sys
import os
from pathlib import Path
import requests

# Ensure repository root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from Commands.truth import format_truth_post, is_valid_post


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
        print(f"\nFormatted Message:\n{format_truth_post(valid_item)}")
    else:
        print("No valid posts found!")


if __name__ == "__main__":
    test_truth_social_api()
