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
    return_str = f"{news_item.title}, published on {news_item.published}, {final_url}"
    print(news_item)
    return return_str

def get_redirect_url(url):
    """hello""" 
    response = requests.get(url, allow_redirects=True)
    return response.url

def get_help_text():
    return "Get a random news headline for a given query. If no query is provided, get a random news headline."

# title = get_random_news_item('ukraine')
 
# if isinstance(title, str):
#     print(f"Title: {title}\nURL: {url}")
# else:
#     print(title)
 
