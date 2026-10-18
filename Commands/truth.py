import re
import time
from typing import Optional, Dict, Any, List
import requests
import feedparser
from bs4 import BeautifulSoup
from Utils.utils import fetch_cmd_data, check_cooldown, CHUNK_SIZE, format_time_ago


def truncate_with_suffix(text: str, suffix: str, max_length: int = CHUNK_SIZE) -> str:
    ellipsis = "..."
    suffix = suffix.strip()
    separator = " " if suffix and text else ""
    total_suffix = ellipsis + separator + suffix  # e.g. "... (posted 10m ago)"

    if len(text) + len(separator + suffix) <= max_length:
        return f"{text}{separator}{suffix}" if suffix else text

    max_text_len = max_length - len(total_suffix)

    if max_text_len <= 0:
        return suffix[:max_length]

    return text[:max_text_len].rstrip() + total_suffix


def is_valid_post(item: dict) -> bool:
    if not isinstance(item, dict):
        return False
    
    raw_text = item.get("text")
    text = raw_text if isinstance(raw_text, str) else ""

    # Check if there is usable text or a fallback URL
    if text.strip() in ["[Video]", "[Image]"]:
        return bool(item.get("post_url") or item.get("image_url") or item.get("video_url"))
    
    return bool(text or item.get("post_url") or item.get("image_url") or item.get("video_url"))


def fetch_trumpstruth_media_map(feed_url: str = "https://www.trumpstruth.org/feed?limit=5", timeout: int = 5) -> Dict[str, Dict[str, Any]]:
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


def enrich_with_trumpstruth_media(item: dict) -> dict:
    """
    Enriches a post item with high-quality source image / video URLs
    from trumpstruth.org if available. Returns the item (modified in-place or original).
    """
    try:
        post_id = str(item.get("id") or "")
        if not post_id and item.get("post_url"):
            match = re.search(r"/(\d+)$", item["post_url"])
            if match:
                post_id = match.group(1)

        trump_media = fetch_trumpstruth_media_map()
        if post_id and post_id in trump_media:
            post_media = trump_media[post_id]
            if post_media.get("videos"):
                item["video_url"] = post_media["videos"][0]
            if post_media.get("images"):
                item["image_url"] = post_media["images"][0]
    except Exception:
        pass

    return item


def fetch_latest_from_rss(feed_url: str = "https://www.trumpstruth.org/feed?limit=5", timeout: int = 5) -> Optional[dict]:
    """
    Parses the trumpstruth.org RSS feed to extract the latest valid post as a fallback
    if the primary Rollcall API is unavailable.
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
            return None
        feed = feedparser.parse(response.text)
    except Exception:
        return None

    for entry in getattr(feed, "entries", []):
        post_id = entry.get("truth_originalid") or ""
        post_url = entry.get("truth_originalurl") or entry.get("link") or ""
        published = entry.get("published") or ""
        post_type = entry.get("archive_posttype") or ""

        desc = entry.get("summary") or entry.get("description") or ""
        soup = BeautifulSoup(desc, "html.parser")

        quote_span = soup.find("span", class_="quote-inline")
        if quote_span:
            quote_span.decompose()

        for bq in soup.find_all("blockquote"):
            bq.decompose()

        for a in soup.find_all("a"):
            txt = a.get_text().strip()
            if txt in ["View image", "View video"]:
                a.decompose()

        text = soup.get_text().strip()

        images: List[str] = []
        videos: List[str] = []
        for media in entry.get("media_content", []):
            url = media.get("url")
            medium = media.get("medium")
            if not url:
                continue
            if medium == "video" or url.endswith((".mp4", ".mov", ".m4v")):
                videos.append(url)
            elif medium == "image" or url.endswith((".jpg", ".jpeg", ".png", ".webp")):
                images.append(url)

        item = {
            "id": post_id,
            "date": published,
            "text": text,
            "post_url": post_url,
            "image_url": images[0] if images else "",
            "video_url": videos[0] if videos else "",
            "social": {
                "repost_flag": post_type == "repost",
                "quote_flag": post_type == "quote",
                "media_count": len(images) + len(videos),
            },
        }

        if is_valid_post(item):
            return item

    return None


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
    
    valid_item = None
    from_rss = False
    max_retries = 3

    # Primary attempt: Rollcall API with up to 3 retries
    for attempt in range(max_retries):
        try:
            response = requests.get(api_url, params=params, headers=headers, timeout=5)
            if response.status_code == 200:
                data = response.json()
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
                        posts = []
                else:
                    posts = []

                for item in posts:
                    if is_valid_post(item):
                        valid_item = item
                        break

                break
        except Exception:
            pass

        if attempt < max_retries - 1:
            time.sleep(0.5)

    # If Rollcall failed or had no valid post, fetch from trumpstruth.org RSS
    if valid_item is None:
        valid_item = fetch_latest_from_rss()
        if valid_item is not None:
            from_rss = True

    if valid_item is None:
        self.send_privmsg(cmd.channel, "Failed to fetch the latest post, please try again later.")
        return

    # Attempt to enrich valid_item with direct source image / video from trumpstruth.org
    # Skip enrichment if the item was already sourced directly from RSS (media already included)
    if not from_rss:
        enrich_with_trumpstruth_media(valid_item)

    message_text = format_truth_post(valid_item)
    self.send_privmsg(cmd.channel, message_text)