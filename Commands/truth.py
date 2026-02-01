import requests
from bs4 import BeautifulSoup
from Utils.utils import fetch_cmd_data, check_cooldown, CHUNK_SIZE, format_time_ago


def truncate_with_suffix(text: str, suffix: str, max_length: int = CHUNK_SIZE) -> str:
    ellipsis = "..."
    space = " " if suffix else ""
    total_suffix = ellipsis + space + suffix  # e.g. "... (posted 10m ago)"

    if len(text) + len(space + suffix) <= max_length:
        return text + space + suffix

    max_text_len = max_length - len(total_suffix)

    if max_text_len <= 0:
        return suffix[:max_length]

    return text[:max_text_len].rstrip() + total_suffix


def is_valid_post(item: dict) -> bool:
    if not isinstance(item, dict):
        return False
    raw_text = item.get("text")
    text = raw_text if isinstance(raw_text, str) else ""
    social = item.get("social") or {}
    if not isinstance(social, dict):
        social = {}
    
    if text.startswith("RT:"):
        return False
    
    if social.get("quote_flag", False):
        return False
    
    if social.get("repost_flag", False):
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
    
    if isinstance(data, list):
        posts = data
    elif isinstance(data, dict):
        if "results" in data and isinstance(data["results"], list):
            posts = data["results"]
        elif "data" in data and isinstance(data["data"], list):
            posts = data["data"]
        elif "items" in data and isinstance(data["items"], list):
            posts = data["items"]
        else:
            self.send_privmsg(cmd.channel, "No posts found in the response.")
            return
    else:
        self.send_privmsg(cmd.channel, "No posts found in the response.")
        return
    
    if not posts:
        self.send_privmsg(cmd.channel, "No posts found in the response.")
        return

    valid_item = None
    clean_text = ""
    time_part = ""

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
                continue # Skip if absolutely no text and no URL
            
        valid_item = item
        clean_text = extracted_text
        post_date = valid_item.get("date", "")
        time_part = format_time_ago(post_date) if post_date else ""
        break

    if valid_item is None:
        self.send_privmsg(cmd.channel, "No valid posts found.")
        return

    max_content_len = CHUNK_SIZE - len("TRUTH ") - 1
    truncated_text = truncate_with_suffix(clean_text, time_part, max_length=max_content_len)
    self.send_privmsg(cmd.channel, "TRUTH " + truncated_text)