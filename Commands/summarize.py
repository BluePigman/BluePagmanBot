import html
import re
from typing import Optional, List

from lxml import etree

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


class TranscriptError(Exception):
    """Base exception for transcript retrieval errors."""
    pass


class TranscriptUnavailableError(TranscriptError):
    """Raised when no captions are found."""
    pass


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


def get_transcript(video_id: str, language: str = "en") -> str:
    """
    Get captions for a given YouTube video using the Innertube API.
    Returns the transcript as a single string.
    Raises TranscriptError or TranscriptUnavailableError on failure.
    """
    video_url = f"https://www.youtube.com/watch?v={video_id}"

    try:
        # Step 1: Fetch the INNERTUBE_API_KEY from the video page
        res = proxy_request("GET", video_url)
        if res.status_code != 200:
            print(f"Failed to fetch video page: {res.status_code}")
            raise TranscriptError(f"Failed to fetch video page: {res.status_code}")

        html_content = res.text
        api_key_match = re.search(r'"INNERTUBE_API_KEY":"([^"]+)"', html_content)
        if not api_key_match:
            print("INNERTUBE_API_KEY not found in page")
            raise TranscriptError("INNERTUBE_API_KEY not found in page")
        api_key = api_key_match.group(1)

        # Step 2: Call the Innertube player API as Android client
        player_endpoint = f"https://www.youtube.com/youtubei/v1/player?key={api_key}"
        player_body = {
            "context": {
                "client": {
                    "clientName": "ANDROID",
                    "clientVersion": "21.02.33"
                }
            },
            "videoId": video_id
        }

        player_res = proxy_request(
            "POST",
            player_endpoint,
            headers={"Content-Type": "application/json",
                     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36"},
            json=player_body
        )
        if player_res.status_code != 200:
            err = f"Failed to fetch player data: {player_res.status_code}"
            print(err)
            raise TranscriptError(err)

        player_data = player_res.json()

        # Step 3: Extract the caption track URL
        tracks = player_data.get("captions", {}).get("playerCaptionsTracklistRenderer", {}).get("captionTracks")
        if not tracks:
            print("No caption tracks found")
            raise TranscriptUnavailableError("No caption tracks found")

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
            raise TranscriptError("No baseUrl in caption track")

        # Remove format parameter if present to get plain XML
        base_url = re.sub(r'&fmt=\w+$', '', base_url)

        # Step 4: Fetch and parse captions XML
        caption_res = proxy_request("GET", base_url)
        if caption_res.status_code != 200:
            print(f"Failed to fetch captions: {caption_res.status_code}")
            raise TranscriptError(f"Failed to fetch captions: {caption_res.status_code}")

        # Use a secure XML parser configuration
        parser = etree.XMLParser(resolve_entities=False, no_network=True, recover=True)
        root = etree.fromstring(caption_res.content, parser=parser)

        captions: List[str] = []
        for text_elem in root.xpath("//text"):
            if text_elem.text:
                decoded_text = html.unescape(text_elem.text)
                captions.append(decoded_text)

        if not captions:
            print("No caption text found in XML")
            raise TranscriptUnavailableError("No caption text found in XML")

        return " ".join(captions)

    except (TranscriptError, TranscriptUnavailableError):
        raise
    except Exception as e:
        log_err(e)
        raise TranscriptError(f"Unexpected error: {e}")


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

        try:
            transcript = get_transcript(video_id)
        except TranscriptUnavailableError:
            self.send_privmsg(cmd.channel, f"{cmd.username}, no transcript available for that video.")
            return
        except TranscriptError as e:
            self.send_privmsg(cmd.channel, f"{cmd.username}, failed to retrieve transcript: {e}")
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
