import feedparser
import random
import requests
from datetime import datetime
from googlenewsdecoder import gnewsdecoder


def get_help_text():
    return "Get a random news headline for a given query. If no query is provided, get a random news headline."

def get_random_news_item(keyword=None):
    url = f"https://news.google.com/rss/search?q={keyword}"
    if not keyword:
        url = "https://news.google.com/rss"
    feed = feedparser.parse(url)
    if feed.bozo != 0:
        return "Failed to retrieve or parse the RSS feed."
    if not feed.entries or len(feed.entries) == 0:
        return "No news found for the given query."
    news_item = random.choice(feed.entries)
    news_url = get_redirect_url(news_item.link)

    try:
        decoded_url = gnewsdecoder(news_url)

        if decoded_url.get("status"):
            final_url = decoded_url["decoded_url"]
        else:
            final_url = "Failed to decode the URL."
    except Exception as e:
        return f"Error occurred: {e}"

    paywalled = [
        "nytimes.com",
        "economist.com"
    ]
    if any(domain in final_url for domain in paywalled):
        final_url = f"https://archive.today/?run=1&url={final_url}"
    return_str = f"{news_item.title}, published on {parse_date(news_item.published)}, {final_url}"
    return return_str

def parse_date(time_str):
    gmt_time = datetime.strptime(time_str, '%a, %d %b %Y %H:%M:%S GMT')
    return gmt_time.strftime('%b %d %Y')

def get_redirect_url(url):
    response = requests.get(url, allow_redirects=True)
    return response.url