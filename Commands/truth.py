import requests
from bs4 import BeautifulSoup
from Utils.utils import fetch_cmd_data, check_cooldown, CHUNK_SIZE, format_time_ago


def truncate_with_suffix(text: str, suffix: str, max_length: int = CHUNK_SIZE) -> str:
    ellipsis = "..."
    space = " " if suffix else ""
    total_suffix = ellipsis + space + suffix  # e.g. "... (posted 10m ago)"

    if len(text) + len(space + suffix) <= max_length:
        return text + space + suffix

    # Reserve space for the suffix and ellipsis
    max_text_len = max_length - len(total_suffix)

    if max_text_len <= 0:
        # Not enough room for even a single char + suffix
        return suffix[:max_length]

    return text[:max_text_len].rstrip() + total_suffix


def is_valid_post(item: dict) -> bool:
    """Check if a post is an original text post (not a retweet, quote, or video-only)."""
    text = item.get("text", "")
    social = item.get("social", {})
    
    # Skip retweets (text starts with "RT:")
    if text.startswith("RT:"):
        return False
    
    # Skip quote posts
    if social.get("quote_flag", False):
        return False
    
    # Skip reposts
    if social.get("repost_flag", False):
        return False
    
    # Skip video-only posts (text is just "[Video]")
    if text.strip() == "[Video]":
        return False
    
    # Skip posts with no actual text content
    if not text.strip():
        return False
    
    return True


def truthsocial(self, message):
    cmd = fetch_cmd_data(self, message)
    if not check_cooldown(cmd.state, cmd.nick, cmd.cooldown):
        return
    
    api_url = "https://rollcall.com/wp-json/factbase/v1/twitter"
    params = {
        "platform": "truth social",
        "sort": "date",
        "sort_order": "desc",
        "page": 1,
        "format": "json"
    }
    
    try:
        response = requests.get(api_url, params=params, timeout=10)
    except requests.exceptions.ReadTimeout:
        self.send_privmsg(cmd.channel,
            "The server did not respond, please try again later.")
        return
    except requests.exceptions.RequestException as e:
        self.send_privmsg(cmd.channel,
            f"Failed to connect to the server: {e}")
        return
    
    if response.status_code != 200:
        self.send_privmsg(cmd.channel,
            f"Failed to fetch the latest post. Status code {response.status_code}")
        return

    try:
        data = response.json()
    except ValueError:
        self.send_privmsg(cmd.channel, "Failed to parse response from server.")
        return
    
    if not data or not isinstance(data, list):
        self.send_privmsg(cmd.channel, "No posts found in the response.")
        return

    # Find the first valid post (not a retweet, quote, or video-only)
    valid_item = None
    for item in data:
        if is_valid_post(item):
            valid_item = item
            break

    if valid_item is None:
        self.send_privmsg(cmd.channel, "No valid posts found.")
        return

    # Get the post date for the time ago suffix
    post_date = valid_item.get("date", "")
    if post_date:
        time_part = format_time_ago(post_date)
    else:
        time_part = ""
    
    # Get the post text and clean it
    post_html = valid_item.get("social", {}).get("post_html", "")
    if post_html:
        clean_text = BeautifulSoup(post_html, "html.parser").get_text().strip()
    else:
        clean_text = valid_item.get("text", "").strip()
    
    # Normalize whitespace (replace multiple spaces/newlines with single space)
    clean_text = " ".join(clean_text.split())
    
    max_content_len = CHUNK_SIZE - len("TRUTH ") - 1
    truncated_text = truncate_with_suffix(clean_text, time_part, max_length=max_content_len)
    self.send_privmsg(cmd.channel, "TRUTH " + truncated_text)