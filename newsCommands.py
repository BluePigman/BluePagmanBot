import feedparser
import random
import requests
import base64, re
 
def get_random_news_item(keyword = None):
    url = f"https://news.google.com/rss/search?q={keyword}"
    if not keyword:
        url = "https://news.google.com/rss"
    
    feed = feedparser.parse(url)
    if feed.bozo != 0:
        return "Failed to retrieve or parse the RSS feed."
    if not feed.entries or len(feed.entries) == 0:
        return "No news found for the given query."
    news_item = random.choice(feed.entries)
    final_url = get_redirect_url(news_item.link)
    print(final_url)
    if final_url.startswith("https://news.google.com/rss/articles/"):
        final_url = decode_url(final_url)
        if not final_url:
            return "Failed to decode the URL."
    # if url is paywalled, try to get from archive.today
    paywalled = [
        "nytimes.com",
        "economist.com"
    ]
    if any(domain in final_url for domain in paywalled):
        final_url = f"https://archive.today/?run=1&url={final_url}"
    return_str = f"{news_item.title}, published on {news_item.published}, {final_url}"
    return return_str

def get_redirect_url(url):
    response = requests.get(url, allow_redirects=True)
    return response.url


def decode_url(google_news_url):
    code_pattern = r'\/articles\/(.*?)\?'
    code_match = re.search(code_pattern , google_news_url)
    if not code_match:
        return "Error: Not a valid link"

    encoded_url = code_match.group(1)

    # Add the missing padding
    missing_padding = len(encoded_url) % 4
    if missing_padding:
        encoded_url += '=' * (4 - missing_padding)

    try:
        decoded_url = str(base64.urlsafe_b64decode(encoded_url), 'utf-8', errors='ignore')
    except Exception as e:
        return str(e)[:390]

    if not decoded_url:
        return "None"
    print(decoded_url)
    url_pattern = r'http.+'
    url_match = re.search(url_pattern , decoded_url, re.IGNORECASE)
    if not url_match:
        # Attempt to find YouTube video ID pattern
        youtube_id_match = re.search(r'([a-zA-Z0-9_-]{11})', decoded_url)
        if youtube_id_match:
            youtube_url = f"https://www.youtube.com/watch?v={youtube_id_match.group(0)}"
            r = requests.get(youtube_url)
            if "Video Unavailable" in r.text:
                return "Error: Youtube video unavailable"
            return youtube_url
        
        return "Error: Unable to decode link", str(decoded_url)

        
    decoded_url = url_match.group(0)
    head, _, _ = decoded_url.partition("\x01")
    return head




def get_help_text():
    return "Get a random news headline for a given query. If no query is provided, get a random news headline."
 
