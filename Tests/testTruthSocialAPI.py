import requests
from bs4 import BeautifulSoup


def is_valid_post(item: dict) -> bool:
    text = item.get("text", "")
    social = item.get("social", {})
    
    if text.startswith("RT:"):
        return False
    if social.get("quote_flag", False):
        return False
    if social.get("repost_flag", False):
        return False
    if text.strip() in ["[Video]", "[Image]"]:
        return False
    if not text.strip():
        return False
    
    return True


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
    
    response = requests.get(api_url, params=params, timeout=10)
    
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
    
    print("\nFirst 5 posts (showing validity):")
    for i, item in enumerate(posts[:5]):
        text = item.get("text", "")[:80]
        valid = is_valid_post(item)
        date = item.get("date", "")
        print(f"\n[{i+1}] Valid: {valid}")
        print(f"    Date: {date}")
        print(f"    Text: {text}...")
    
    print("\n" + "=" * 60)
    print("FIRST VALID POST (not a retweet):")
    print("=" * 60)
    
    valid_item = None
    clean_text = ""
    
    for item in posts:
        if not is_valid_post(item):
            continue
            
        social = item.get("social") or {}
        if not isinstance(social, dict):
            social = {}
            
        post_html = social.get("post_html", "")
        if post_html:
            extracted_text = BeautifulSoup(post_html, "html.parser").get_text().strip()
        else:
            extracted_text = item.get("text", "").strip()
            
        extracted_text = " ".join(extracted_text.split())
        
        # If text is a placeholder, try to use the post URL or image URL
        if not extracted_text or extracted_text in ["[Video]", "[Image]"]:
            # Priority: post_url > image_url > placeholder text
            fallback_url = item.get("post_url") or item.get("image_url")
            if fallback_url:
                extracted_text = fallback_url
            elif not extracted_text:
                continue
            
        valid_item = item
        clean_text = extracted_text
        break
        
    if valid_item:
        print(f"\nDate: {valid_item.get('date', 'N/A')}")
        print(f"Post URL: {valid_item.get('post_url', 'N/A')}")
        print(f"\nContent:\n{clean_text}")
    else:
        print("No valid posts found!")


if __name__ == "__main__":
    test_truth_social_api()
