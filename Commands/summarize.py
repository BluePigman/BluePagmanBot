import re
import time
from Commands import gemini
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from xml.etree.ElementTree import ParseError
from xml.parsers.expat import ExpatError


def _retry_operation(func, attempts=10, delay=2):
    """Retry a function multiple times in case of XML parsing errors."""
    for attempt in range(attempts):
        try:
            return func()
        except (ParseError, ExpatError):
            if attempt == attempts - 1:  # If this was the last attempt
                print(f"Failed after {attempts} attempts")
                raise
            print(f"Retrying operation after error (attempt {attempt+1}/{attempts})")
            time.sleep(delay)


def reply_with_summarize(self, message):
    if (message['source']['nick'] not in self.state or time.time() - self.state[message['source']['nick']] >
            self.cooldown):
        self.state[message['source']['nick']] = time.time()

    if not message['command']['botCommandParams']:
        m = f"@{message['tags']['display-name']}, please provide a youtube URL link to summarize."
        self.send_privmsg(message['command']['channel'], m)
        return

    prompt = (message['command']['botCommandParams'])
    if "youtube.com" in prompt or "youtu.be" in prompt:
        video_id = extract_youtube_id(prompt)
        if not video_id:
            self.send_privmsg(message['command']
                              ['channel'], "Youtube vid not found.")
            return
        transcript = get_transcript(video_id)
        if not transcript or len(transcript) < 1:
            self.send_privmsg(
                message['command']['channel'], "No transcript found for the video.")
            return
        prompt = f"Here is the transcript for a youtube video, please summarize it in under 500 characters, \
        ignoring any sponsors of the video or mention of interacting with their channel (Subscribing, liking, etc): {transcript}"
    else:
        self.send_privmsg(message['command']['channel'],
                          "Please provide a Youtube link to summarize.")
        return
    result = gemini.generate(prompt)
    for m in result:
        self.send_privmsg(message['command']['channel'], m)
        time.sleep(1)


def extract_youtube_id(text):
    youtube_regex = r"(https?://)?(www\.|m\.)?(youtube\.com|youtu\.be)/.+$"

    match = re.search(youtube_regex, text)
    video_id = None
    if match:
        if "youtube.com/watch" in text:
            video_id = text.split("v=")[-1].split("&")[0]
        elif "youtube.com/shorts" in text:
            video_id = text.split("/shorts/")[-1].split("?")[0]
        elif "youtu.be" in text:
            video_id = text.split("/")[-1].split("?")[0]
    return video_id


def get_transcript(video_id: str) -> str | None:
    # Try getting English transcript, fallback on translated transcript
    try:
        # Use the retry operation for listing transcripts
        def list_transcripts_operation():
            return YouTubeTranscriptApi.list_transcripts(video_id)
        
        transcript_list = _retry_operation(list_transcripts_operation)

        try:
            transcript = transcript_list.find_transcript(['en-GB'])
        except NoTranscriptFound:
            try:
                transcript = transcript_list.find_transcript(['en'])
            except NoTranscriptFound:
                for t in transcript_list:
                    try:
                        # Use the retry operation for translation
                        def translate_operation():
                            return t.translate('en')
                        
                        transcript = _retry_operation(translate_operation)
                        break
                    except Exception as e:
                        print(f"Translation error: {e}")
                        continue
                else:
                    return None

        # Use the retry operation for fetching the transcript
        def fetch_operation():
            return transcript.fetch()
        
        fetched = _retry_operation(fetch_operation)
        
        # Check if fetched has a 'snippets' attribute, otherwise treat it as the transcript list directly
        if hasattr(fetched, 'snippets'):
            merged_text = " ".join(snippet.text.replace(r'\'', "'") for snippet in fetched.snippets)
        else:
            merged_text = " ".join(item['text'].replace(r'\'', "'") for item in fetched)
        
        return merged_text

    except (NoTranscriptFound, TranscriptsDisabled):
        print("Transcripts are disabled or none were found.")
        return None
    except Exception as e:
        print(f"Unexpected error for video {video_id}: {e}")
        return None