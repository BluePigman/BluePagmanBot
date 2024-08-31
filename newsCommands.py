import feedparser
import random
import requests
import base64
from datetime import datetime
from zoneinfo import ZoneInfo
import json
from urllib.parse import quote, urlparse
from selectolax.parser import HTMLParser

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
    if news_url.startswith("https://news.google.com/rss/articles/"):
        final_url = decode_google_news_url(news_url)
        if final_url["status"] == False:
            print(final_url["message"])
            final_url = "Failed to decode the URL."
        else:
            final_url = final_url["decoded_url"]
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
    """Decodes a Google News URL using the updated API-based method."""
    try:
        base64_str_response = get_base64_str(source_url)
        if not base64_str_response["status"]:
            return base64_str_response

        decoding_params_response = get_decoding_params(
            base64_str_response["base64_str"]
        )
        if not decoding_params_response["status"]:
            return decoding_params_response

        signature = decoding_params_response["signature"]
        timestamp = decoding_params_response["timestamp"]
        base64_str = decoding_params_response["base64_str"]

        decoded_url_response = decode_url(signature, timestamp, base64_str)
        if not decoded_url_response["status"]:
            return decoded_url_response

        return {"status": True, "decoded_url": decoded_url_response["decoded_url"]}
    except Exception as e:
        return {
            "status": False,
            "message": f"Error in decode_google_news_url: {str(e)}",
        }
    
def get_base64_str(source_url):
    try:
        url = urlparse(source_url)
        path = url.path.split("/")
        if (
            url.hostname == "news.google.com"
            and len(path) > 1
            and path[-2] in ["articles", "read"]
        ):
            base64_str = path[-1]
            return {"status": True, "base64_str": base64_str}
        else:
            return {"status": False, "message": "Invalid Google News URL format."}
    except Exception as e:
        return {"status": False, "message": f"Error in get_base64_str: {str(e)}"}

def get_decoding_params(base64_str):
    try:
        response = requests.get(f"https://news.google.com/articles/{base64_str}")
        response.raise_for_status()

        parser = HTMLParser(response.text)
        datas = parser.css_first("c-wiz > div[jscontroller]")
        if datas is None:
            return {
                "status": False,
                "message": "Failed to fetch data attributes from Google News.",
            }

        return {
            "status": True,
            "signature": datas.attributes.get("data-n-a-sg"),
            "timestamp": datas.attributes.get("data-n-a-ts"),
            "base64_str": base64_str,
        }
    except requests.exceptions.RequestException as req_err:
        return {
            "status": False,
            "message": f"Request error in get_decoding_params: {str(req_err)}",
        }
    except Exception as e:
        return {"status": False, "message": f"Error in get_decoding_params: {str(e)}"}


def decode_url(signature, timestamp, base64_str):
    try:
        url = "https://news.google.com/_/DotsSplashUi/data/batchexecute"

        payload = [
            "Fbv4je",
            f'["garturlreq",[["X","X",["X","X"],null,null,1,1,"US:en",null,1,null,null,null,null,null,0,1],"X","X",1,[1,1,1],1,1,null,0,0,null,0],"{base64_str}",{timestamp},"{signature}"]',
        ]
        headers = {
            "content-type": "application/x-www-form-urlencoded;charset=UTF-8",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        }
        response = requests.post(
            url, headers=headers, data=f"f.req={quote(json.dumps([[payload]]))}"
        )
        response.raise_for_status()

        parsed_data = json.loads(response.text.split("\n\n")[1])[:-2]
        decoded_url = json.loads(parsed_data[0][2])[1]

        return {"status": True, "decoded_url": decoded_url}
    except requests.exceptions.RequestException as req_err:
        return {
            "status": False,
            "message": f"Request error in decode_url: {str(req_err)}",
        }
    except (json.JSONDecodeError, IndexError, TypeError) as parse_err:
        return {
            "status": False,
            "message": f"Parsing error in decode_url: {str(parse_err)}",
        }
    except Exception as e:
        return {"status": False, "message": f"Error in decode_url: {str(e)}"}

