import re, requests
from typing import Iterable, Optional
from config import YT_CAPTION_API_TOKEN, YT_CAPTION_API_URL
from Utils.utils import (
    fetch_cmd_data,
    check_cooldown,
    send_chunks,
    clean_str,
    gemini_generate
)

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


def extract_youtube_id(text: str) -> Optional[str]:
    youtube_regex = r"(?:youtu\.be/|youtube\.com/(?:watch\?v=|shorts/))([A-Za-z0-9_-]{11})"
    match = re.search(youtube_regex, text)
    return match.group(1) if match else None


def get_transcript(video_id: str, languages: Iterable[str] = ("en",)) -> str:
    language = next(iter(languages), "en")
    endpoint = f"{YT_CAPTION_API_URL.rstrip('/')}/transcript/{video_id}"
    headers = {"X-AccessToken": YT_CAPTION_API_TOKEN}
    params = {
        "language": language,
        "include_meta": "false",
    }

    try:
        response = requests.get(endpoint, headers=headers, params=params, timeout=30)
    except requests.RequestException as e:
        print(f"[summarize] Transcript API request exception for {video_id}: {e}")
        raise TranscriptError("Failed to contact transcript API.") from e

    if response.status_code == 404:
        raise TranscriptUnavailableError("No transcript available for that video.")

    if response.status_code in {401, 403}:
        raise TranscriptError("Transcript API authentication failed.")

    if response.status_code >= 400:
        try:
            detail = response.json().get("detail", response.text)
        except ValueError:
            detail = response.text
        print(
            f"[summarize] Transcript API error for {video_id}: "
            f"status={response.status_code} detail={detail}"
        )
        raise TranscriptError("Transcript API request failed.")

    try:
        payload = response.json()
    except ValueError as e:
        print(f"[summarize] Transcript API invalid JSON for {video_id}: {e}")
        raise TranscriptError("Transcript API returned invalid JSON.") from e

    transcript = payload.get("transcript", "").strip()
    if not transcript:
        raise TranscriptUnavailableError("Transcript returned, but was empty.")

    return transcript


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
            print(summary)
            self.send_privmsg(cmd.channel, f"{cmd.username}, failed to generate a summary. Please try again later.")
            return

        send_chunks(self.send_privmsg, cmd.channel, clean_str(summary, ["`", "*"]))
    except Exception as e:
        print(f"[Error] {e}")
        self.send_privmsg(cmd.channel, "Failed to generate a summary. Please try again later.")
        return
