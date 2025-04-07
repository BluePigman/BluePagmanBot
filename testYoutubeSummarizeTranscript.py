import re
from Commands import gemini
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound

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
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

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
                        transcript = t.translate('en')
                        break
                    except Exception:
                        continue
                else:
                    print("No translatable transcripts available.")
                    return None

        # Fetch the transcript text
        fetched = transcript.fetch()
        # Join all snippet texts together with spaces
        merged_text = " ".join(snippet.text.replace(r'\'', "'") for snippet in fetched.snippets)
        return merged_text

    except (NoTranscriptFound, TranscriptsDisabled):
        print("Transcripts are disabled or none were found.")
        return None
    except Exception as e:
        print(f"Unexpected error for video {video_id}: {e}")
        return None
print(get_transcript("Z6NUxfhKvzo"))