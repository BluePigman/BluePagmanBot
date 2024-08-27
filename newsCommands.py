import feedparser
import random
import requests
import base64
from datetime import datetime
from zoneinfo import ZoneInfo

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
    final_url = get_redirect_url(news_item.link)
    if final_url.startswith("https://news.google.com/rss/articles/"):
        final_url = decode_google_news_url(final_url)
        if not final_url:
            return "Failed to decode the URL."
    # if url is paywalled, try to get from archive.today
    paywalled = [
        "nytimes.com",
        "economist.com"
    ]
    if any(domain in final_url for domain in paywalled):
        final_url = f"https://archive.today/?run=1&url={final_url}"
    return_str = f"{news_item.title}, published on {gmt_to_est(news_item.published)}, {final_url}"
    return return_str

def gmt_to_est(gmt_time_str):
    gmt_time = datetime.strptime(gmt_time_str, '%a, %d %b %Y %H:%M:%S GMT')
    gmt_time = gmt_time.replace(tzinfo=ZoneInfo('GMT'))
    est_time = gmt_time.astimezone(ZoneInfo('America/New_York'))
    return est_time.strftime('%a, %d %b %Y %I:%M:%S %p EST')

def get_redirect_url(url):
    response = requests.get(url, allow_redirects=True)
    return response.url

def decode_google_news_url(source_url):
    url = requests.utils.urlparse(source_url)
    path = url.path.split("/")
    if url.hostname == "news.google.com" and len(path) > 1 and path[-2] == "articles":
        base64_str = path[-1]
        decoded_bytes = base64.urlsafe_b64decode(base64_str + "==")
        decoded_str = decoded_bytes.decode("latin1")

        prefix = b"\x08\x13\x22".decode("latin1")
        if decoded_str.startswith(prefix):
            decoded_str = decoded_str[len(prefix):]

        suffix = b"\xd2\x01\x00".decode("latin1")
        if decoded_str.endswith(suffix):
            decoded_str = decoded_str[:-len(suffix)]

        bytes_array = bytearray(decoded_str, "latin1")
        length = bytes_array[0]
        if length >= 0x80:
            decoded_str = decoded_str[2:length + 1]
        else:
            decoded_str = decoded_str[1:length + 1]

        if decoded_str.startswith("AU_yqL"):
            return fetch_decoded_batch_execute(base64_str)

        return decoded_str
    else:
        return source_url

def get_help_text():
    return "Get a random news headline for a given query. If no query is provided, get a random news headline."

def fetch_decoded_batch_execute(id):
    s = (
        '[[["Fbv4je","[\\"garturlreq\\",[[\\"en-US\\",\\"US\\",[\\"FINANCE_TOP_INDICES\\",\\"WEB_TEST_1_0_0\\"],'
        'null,null,1,1,\\"US:en\\",null,180,null,null,null,null,null,0,null,null,[1608992183,723341000]],'
        '\\"en-US\\",\\"US\\",1,[2,3,4,8],1,0,\\"655000234\\",0,0,null,0],\\"'
        + id
        + '\\"]",null,"generic"]]]'
    )

    headers = {
        "Content-Type": "application/x-www-form-urlencoded;charset=utf-8",
        "Referer": "https://news.google.com/",
    }

    response = requests.post(
        "https://news.google.com/_/DotsSplashUi/data/batchexecute?rpcids=Fbv4je",
        headers=headers,
        data={"f.req": s},
    )

    if response.status_code != 200:
        return "Failed to fetch data from Google."

    text = response.text
    header = '[\\"garturlres\\",\\"'
    footer = '\\",'
    if header not in text:
        raise Exception(f"Header not found in response: {text}")
    start = text.split(header, 1)[1]
    if footer not in start:
        raise Exception("Footer not found in response.")
    url = start.split(footer, 1)[0]
    if r"\\u003d" in url:
        url = url.replace(r"\\u003d", "=")
    return url
