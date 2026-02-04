import random
import re
import time
from typing import Iterable
from typing import Optional

from google import genai
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound, InvalidVideoId, \
    VideoUnavailable
from youtube_transcript_api.proxies import WebshareProxyConfig

from Utils.utils import (
    fetch_cmd_data,
    check_cooldown,
    send_chunks,
    clean_str,
    gemini_generate
)
try:
    from config import YT_PROXY_PASSWORD, YT_PROXY_USERNAME
except ImportError:
    YT_PROXY_PASSWORD = None
    YT_PROXY_USERNAME = None

SUMMARY_CHAR_LIMIT = 500


class TranscriptError(Exception):
    """Base exception for transcript retrieval errors."""
    pass


class TranscriptUnavailableError(TranscriptError):
    """Raised when no captions are found."""
    pass


MODEL_NAME = "gemini-flash-lite-latest"
GENERATION_CONFIG = {
    "max_output_tokens": 400,
    "temperature": 0.5,
    "top_p": 0.95,
}


def build_ytt_api():
    if YT_PROXY_USERNAME and YT_PROXY_PASSWORD:
        return YouTubeTranscriptApi(
            proxy_config=WebshareProxyConfig(
                proxy_username=YT_PROXY_USERNAME,
                proxy_password=YT_PROXY_PASSWORD,
            )
        )
    else:
        # No proxy configured
        return YouTubeTranscriptApi()


ytt_api = build_ytt_api()


def extract_youtube_id(text: str) -> Optional[str]:
    youtube_regex = r"(?:youtu\.be/|youtube\.com/(?:watch\?v=|shorts/))([A-Za-z0-9_-]{11})"
    match = re.search(youtube_regex, text)
    return match.group(1) if match else None


def _join_fetched_transcript(transcript) -> str:
    """
    transcript is a FetchedTranscript (iterable of FetchedTranscriptSnippet)
    """
    return " ".join(
        s.text.strip()
        for s in transcript
        if getattr(s, "text", None) and s.text.strip()
    )


def get_transcript(video_id: str, languages: Iterable[str] = ("en",)) -> str:
    """
    Get captions for a given YouTube video using youtube_transcript_api fetch().
    Returns the transcript as a single string.
    Raises TranscriptError or TranscriptUnavailableError on failure.
    """

    # The library already retries internally for RequestBlocked according to:
    # proxy_config.retries_when_blocked (Webshare defaults to 10).
    #
    # Outer retry here is mainly for things the internal retry usually won't cover:
    # - IpBlocked (often 429)
    # - YouTubeRequestFailed (proxy flakiness / 5xx / transient HTTP)
    #
    # If you want *zero* manual retry, set attempts=1.
    attempts = 10

    last_err: Optional[Exception] = None

    for i in range(attempts):
        try:
            fetched = ytt_api.fetch(video_id, languages=list(languages))
            text = _join_fetched_transcript(fetched)

            if not text:
                raise TranscriptUnavailableError("Transcript returned, but was empty.")

            return text

        except (NoTranscriptFound, TranscriptsDisabled) as e:
            raise TranscriptUnavailableError(str(e)) from e

        except (InvalidVideoId, VideoUnavailable) as e:
            raise TranscriptError(str(e)) from e

        except Exception as e:
            last_err = e
            if i == attempts - 1:
                break

            time.sleep(0.75)
            continue

    raise TranscriptError(f"Failed to retrieve transcript after retries: {last_err}") from last_err


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
            transcript = get_transcript(video_id, languages=("en",))
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

        summary = gemini_generate(prompt, MODEL_NAME, GENERATION_CONFIG)
        if isinstance(summary, str) and summary.lower().startswith("error"):
            self.send_privmsg(cmd.channel, f"{cmd.username}, failed to generate a summary. Please try again later.")
            return

        send_chunks(self.send_privmsg, cmd.channel, clean_str(summary, ["`", "*"]))
    except Exception as e:
        print(f"[Error] {e}")
        self.send_privmsg(cmd.channel, "Failed to generate a summary. Please try again later.")
        return
