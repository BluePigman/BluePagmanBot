import re
from typing import Optional, Dict, Any
import requests
import feedparser
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
    
    # We now allow retweets (RT:, repost_flag, quote_flag)
    # Check if there is usable text or a fallback URL
    if text.strip() in ["[Video]", "[Image]"]:
        return bool(item.get("post_url") or item.get("image_url") or item.get("video_url"))
    
    return bool(text or item.get("post_url") or item.get("image_url") or item.get("video_url"))


def fetch_trumpstruth_media_map(feed_url: str = "https://www.trumpstruth.org/feed", timeout: int = 5) -> Dict[str, Dict[str, Any]]:
    """
    Parses the trumpstruth.org RSS feed using feedparser to map Truth Social post IDs
    to high-quality source media (direct attachment images and video URLs).
    Returns a dict: { post_id: {"images": [...], "videos": [...]} }
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "application/rss+xml, application/xml, text/xml;q=0.9, */*;q=0.8",
    }
    
    try:
        response = requests.get(feed_url, headers=headers, timeout=timeout)
        if response.status_code != 200:
            return {}
        feed = feedparser.parse(response.text)
    except Exception:
        return {}

    media_map: Dict[str, Dict[str, Any]] = {}
    for entry in getattr(feed, "entries", []):
        post_id = entry.get("truth_originalid")
        if not post_id:
            # Fallback to parsing ID from originalurl or link
            raw_url = entry.get("truth_originalurl") or entry.get("link") or ""
            match = re.search(r"/(\d+)$", raw_url)
            if match:
                post_id = match.group(1)

        if not post_id:
            continue

        images = []
        videos = []

        # Parse media attachments from media_content (Media RSS tags)
        for media in entry.get("media_content", []):
            m_url = media.get("url")
            m_type = media.get("medium")
            if not m_url:
                continue

            if m_type == "video" or m_url.endswith((".mp4", ".mov", ".m4v")):
                videos.append(m_url)
            elif m_type == "image" or m_url.endswith((".jpg", ".jpeg", ".png", ".webp")):
                images.append(m_url)

        # Fallback to enclosures if media_content wasn't populated
        if not images and not videos:
            for enc in entry.get("enclosures", []):
                e_url = enc.get("href") or enc.get("url")
                e_type = enc.get("type", "")
                if not e_url:
                    continue
                if "video" in e_type or e_url.endswith((".mp4", ".mov", ".m4v")):
                    videos.append(e_url)
                elif "image" in e_type or e_url.endswith((".jpg", ".jpeg", ".png", ".webp")):
                    images.append(e_url)

        media_map[post_id] = {
            "images": images,
            "videos": videos,
        }

    return media_map


def format_truth_post(item: dict) -> str:
    raw_text = (item.get("text") or "").strip()
    social = item.get("social") or {}
    if not isinstance(social, dict):
        social = {}

    is_rt = (
        raw_text.startswith("RT:")
        or raw_text.startswith("RT @")
        or bool(social.get("repost_flag"))
        or bool(social.get("quote_flag"))
    )

    post_html = social.get("post_html", "")
    if post_html:
        soup = BeautifulSoup(post_html, "html.parser")
        quote_span = soup.find("span", class_="quote-inline")
        if quote_span:
            quote_span.decompose()
        extracted_text = soup.get_text().strip()
    else:
        extracted_text = raw_text

    # If raw text was used or quote URL remained in text, strip the quote URL prefix
    if extracted_text.startswith("RT:"):
        parts = extracted_text.split(None, 2)
        if len(parts) >= 2 and (parts[1].startswith("http://") or parts[1].startswith("https://")):
            extracted_text = parts[2].strip() if len(parts) == 3 else ""

    extracted_text = " ".join(extracted_text.split())

    prefix = "TRUTH RT: " if is_rt else "TRUTH "
    post_date = item.get("date", "")
    time_part = format_time_ago(post_date) if post_date else ""

    is_video = (extracted_text == "[Video]" or raw_text == "[Video]")
    is_image = (extracted_text == "[Image]" or raw_text == "[Image]")

    post_url = item.get("post_url", "")
    image_url = item.get("image_url", "")
    video_url = item.get("video_url", "")
    media_count = social.get("media_count")

    # Determine primary media URL (prefer direct video, then image, then post link)
    media_url = video_url or image_url

    if is_video:
        # Video post, no caption: video link or post link
        target_url = media_url or post_url
        content = f"{target_url} {time_part}".strip()
        return prefix + content
    elif is_image or not extracted_text:
        # Image post with no caption, or post with only media / empty text
        target_url = media_url or post_url
        content = f"{target_url} {time_part}".strip()
        return prefix + content
    elif media_count or is_rt or video_url:
        # Post with caption and attached media (or RT with attached media)
        suffix_parts = []
        if media_url:
            suffix_parts.append(media_url)
        if time_part:
            suffix_parts.append(time_part)
        suffix = " ".join(suffix_parts)
        max_content_len = CHUNK_SIZE - len(prefix)
        truncated = truncate_with_suffix(extracted_text, suffix, max_length=max_content_len)
        return prefix + truncated
    else:
        # Text only post
        max_content_len = CHUNK_SIZE - len(prefix)
        truncated = truncate_with_suffix(extracted_text, time_part, max_length=max_content_len)
        return prefix + truncated


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
    
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "en,en-US;q=0.9",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(api_url, params=params, headers=headers, timeout=10)
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
    for item in posts:
        if is_valid_post(item):
            valid_item = item
            break

    if valid_item is None:
        self.send_privmsg(cmd.channel, "No valid posts found.")
        return

    # Attempt to enrich valid_item with direct source image / video from trumpstruth.org
    try:
        post_id = str(valid_item.get("id") or "")
        if not post_id and valid_item.get("post_url"):
            match = re.search(r"/(\d+)$", valid_item["post_url"])
            if match:
                post_id = match.group(1)

        trump_media = fetch_trumpstruth_media_map()
        if post_id and post_id in trump_media:
            post_media = trump_media[post_id]
            if post_media.get("videos"):
                valid_item["video_url"] = post_media["videos"][0]
            if post_media.get("images"):
                valid_item["image_url"] = post_media["images"][0]
    except Exception:
        # Fallback cleanly to rollcall image_url / post_url
        pass

    message_text = format_truth_post(valid_item)
    self.send_privmsg(cmd.channel, message_text)