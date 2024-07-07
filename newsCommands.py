import feedparser
import random
import requests
 
def get_random_news_item(keyword = None):
    url = f"https://news.google.com/rss/search?q={keyword}"
    if not keyword:
        url = "https://news.google.com/rss"
    
    feed = feedparser.parse(url)
    if feed.bozo != 0:
        return "Failed to retrieve or parse the RSS feed."
 
    news_item = random.choice(feed.entries)
    final_url = get_redirect_url(news_item.link)
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

def get_help_text():
    return "Get a random news headline for a given query. If no query is provided, get a random news headline."
 
