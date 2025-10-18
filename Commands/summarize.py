import re
import json
from typing import Optional
from urllib.parse import urljoin
import google.generativeai as genai
from Utils.utils import (
    fetch_cmd_data,
    check_cooldown,
    send_chunks,
    clean_str,
    gemini_generate,
    proxy_request
)

SUMMARY_CHAR_LIMIT = 500

model = genai.GenerativeModel(
    model_name="gemini-2.5-flash-lite",
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

def get_transcript(video_id: str) -> str | None:
    base = "https://inv.nadeko.net"
    try:
        res = proxy_request("GET", f"{base}/api/v1/captions/{video_id}")
        if res.status_code != 200:
            return

        data = json.loads(res.text)
        captions = data.get("captions", [])
        if not captions:
            return

        preferred = [
            "English (United States)",
            "English (United Kingdom)",
            "English (auto-generated)",
        ]

        selected = None
        for label in preferred:
            for caption in captions:
                if caption.get("label") == label:
                    selected = caption
                    break
            if selected:
                break

        if not selected and captions:
            selected = captions[0]

        if not selected or not selected.get("url"):
            return

        full_url = urljoin(base, selected["url"])
        transcript_res = proxy_request("GET", full_url)
        if transcript_res.status_code != 200:
            return

        transcript = transcript_res.text
        print(f"Excerpt:\n{transcript[:300]}")
        return transcript

    except Exception as e:
        print(f"Error: {e}")
        return

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