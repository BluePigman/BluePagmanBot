import html
import re
from typing import Optional, List
from xml.etree import ElementTree

import google.generativeai as genai

from Utils.utils import (
    fetch_cmd_data,
    check_cooldown,
    send_chunks,
    clean_str,
    gemini_generate,
    proxy_request,
    log_err
)

SUMMARY_CHAR_LIMIT = 500

model = genai.GenerativeModel(
    model_name="gemini-flash-lite-latest",
    generation_config={
        "max_output_tokens": 400,
        "temperature": 0.5,
        "top_p": 0.95,
    }
)


def extract_youtube_id(text: str) -> Optional[str]:
    youtube_regex = r"(?:youtu\.be/|youtube\.com/(?:watch\?v=|shorts/))([A-Za-z0-9_-]{11})"
    match = re.search(youtube_regex, text)
    return match.group(1) if match else None


def get_transcript(video_id: str, language: str = "en") -> Optional[str]:
    """
    Get captions for a given YouTube video using the Innertube API.
    Returns the transcript as a single string, or None on failure.
    """
    video_url = f"https://www.youtube.com/watch?v={video_id}"

    try:
        # Step 1: Fetch the INNERTUBE_API_KEY from the video page
        res = proxy_request("GET", video_url)
        if res.status_code != 200:
            print(f"Failed to fetch video page: {res.status_code}")
            return None

        html_content = res.text
        api_key_match = re.search(r'"INNERTUBE_API_KEY":"([^"]+)"', html_content)
        if not api_key_match:
            print("INNERTUBE_API_KEY not found in page")
            return None
        api_key = api_key_match.group(1)

        # Step 2: Call the Innertube player API as Android client
        player_endpoint = f"https://www.youtube.com/youtubei/v1/player?key={api_key}"
        player_body = {
            "context": {
                "client": {
                    "clientName": "ANDROID",
                    "clientVersion": "20.10.38"
                }
            },
            "videoId": video_id
        }

        player_res = proxy_request(
            "POST",
            player_endpoint,
            headers={"Content-Type": "application/json"},
            json=player_body,
            bypass_proxy=True
        )
        if player_res.status_code != 200:
            print(f"Failed to fetch player data: {player_res.status_code}")
            return None

        player_data = player_res.json()

        # Step 3: Extract the caption track URL
        tracks = player_data.get("captions", {}).get("playerCaptionsTracklistRenderer", {}).get("captionTracks")
        if not tracks:
            print("No caption tracks found")
            return None

        # Try to find the requested language, fall back to first available
        track = None
        for t in tracks:
            if t.get("languageCode") == language:
                track = t
                break

        if not track:
            # Try English variants
            for t in tracks:
                if t.get("languageCode", "").startswith("en"):
                    track = t
                    break

        if not track:
            # Use first available track
            track = tracks[0]
            print(f"Using fallback language: {track.get('languageCode')}")

        base_url = track.get("baseUrl")
        if not base_url:
            print("No baseUrl in caption track")
            return None

        # Remove format parameter if present to get plain XML
        base_url = re.sub(r'&fmt=\w+$', '', base_url)

        # Step 4: Fetch and parse captions XML
        caption_res = proxy_request("GET", base_url)
        if caption_res.status_code != 200:
            print(f"Failed to fetch captions: {caption_res.status_code}")
            return None

        xml_content = caption_res.text
        root = ElementTree.fromstring(xml_content)

        captions: List[str] = []
        for text_elem in root.findall('text'):
            if text_elem.text:
                decoded_text = html.unescape(text_elem.text)
                captions.append(decoded_text)

        if not captions:
            print("No caption text found in XML")
            return None

        transcript = " ".join(captions)
        return transcript

    except Exception as e:
        log_err(e)
        return None


def reply_with_summarize(self, message):
    try:
        cmd = fetch_cmd_data(self, message)

        if not check_cooldown(cmd.state, cmd.nick, cmd.cooldown):
            return

        if not cmd.params:
            self.send_privmsg(cmd.channel, f"{cmd.username}, please provide a YouTube link to summarize.")
            return

        url = cmd.params.strip()
        if "youtube.com" not in url and "youtu.be" not in url:
            self.send_privmsg(cmd.channel, f"{cmd.username}, that doesn't look like a YouTube link.")
            return

        video_id = extract_youtube_id(url)
        if not video_id:
            self.send_privmsg(cmd.channel, f"{cmd.username}, unable to extract a video ID from that link.")
            return

        transcript = get_transcript(video_id)
        if not transcript:
            self.send_privmsg(cmd.channel, f"{cmd.username}, no transcript available for that video.")
            return

        prompt = {
            "prompt": (
                f"Summarize the following YouTube transcript in under {SUMMARY_CHAR_LIMIT} "
                "characters. Ignore sponsor segments and calls to subscribe/like/etc. "
                "Give your summarization in English only."
            ),
            "grounded": True,
            "grounding_text": clean_str(transcript),
        }

        summary = gemini_generate(prompt, model)
        if isinstance(summary, str) and summary.lower().startswith("error"):
            self.send_privmsg(cmd.channel, f"{cmd.username}, failed to generate a summary. Please try again later.")
            return

        send_chunks(self.send_privmsg, cmd.channel, clean_str(summary, ["`", "*"]))

    except Exception as e:
        print(f"[Error] {e}")
        self.send_privmsg(cmd.channel, "Failed to generate a summary. Please try again later.")
        return
