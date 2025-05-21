import re
import time
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from xml.etree.ElementTree import ParseError
from xml.parsers.expat import ExpatError

def _retry_operation(func, attempts=3, delay=5):
    """Retry a function multiple times in case of XML parsing errors."""
    for attempt in range(attempts):
        try:
            return func()
        except (ParseError, ExpatError):
            if attempt == attempts - 1:  # If this was the last attempt
                print(f"Failed after {attempts} attempts")
                raise
            print(f"Retrying operation after XML parsing error (attempt {attempt+1}/{attempts})")
            time.sleep(delay)

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
    """Get the best available transcript for a video and return the merged text."""
    try:
        print(f"Fetching transcript list for video ID: {video_id}")
        
        # Use retry for listing transcripts
        def list_transcripts_operation():
            return YouTubeTranscriptApi.list_transcripts(video_id)
        
        transcript_list = _retry_operation(list_transcripts_operation)

        # Try to get manually created English transcript first
        print("Attempting to get manually created 'en-GB' transcript...")
        try:
            transcript = transcript_list.find_transcript(['en-GB'])
        except NoTranscriptFound:
            print("No 'en-GB' transcript found, trying auto-generated 'en' transcript...")
            try:
                transcript = transcript_list.find_transcript(['en'])
            except NoTranscriptFound:
                print("No English transcript found, attempting translation from another language...")
                for t in transcript_list:
                    try:
                        # Use retry for transcript translation
                        def translate_operation():
                            return t.translate('en')
                        
                        transcript = _retry_operation(translate_operation)
                        print(f"Successfully translated transcript from {t.language}")
                        break
                    except Exception as e:
                        print(f"Translation error for language {t.language}: {e}")
                        continue
                else:
                    print("No translatable transcripts available.")
                    return None

        # Fetch the transcript text with retry
        print("Fetching transcript content...")
        def fetch_operation():
            return transcript.fetch()
        
        fetched = _retry_operation(fetch_operation)
        
        # Check if fetched has snippets attribute
        if hasattr(fetched, 'snippets'):
            merged_text = " ".join(snippet.text.replace(r'\'', "'") for snippet in fetched.snippets)
        else:
            # Handle the case where fetched is just a list of transcript items
            merged_text = " ".join(item['text'].replace(r'\'', "'") for item in fetched)
        
        print(f"Successfully fetched transcript ({len(merged_text)} characters)")
        return merged_text

    except (NoTranscriptFound, TranscriptsDisabled):
        print("Transcripts are disabled or none were found.")
        return None
    except Exception as e:
        print(f"Unexpected error for video {video_id}: {e}")
        return None

# Test with the video ID
video_id = "eVj2M6BYd_s"
print(f"Testing transcript retrieval for video: {video_id}")
transcript = get_transcript(video_id)
if transcript:
    print(f"Transcript excerpt (first 200 chars): {transcript[:200]}...")
    print(f"Total transcript length: {len(transcript)} characters")
else:
    print("Failed to retrieve transcript")