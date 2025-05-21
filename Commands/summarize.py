import re
import time
from Commands import gemini
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from xml.etree.ElementTree import ParseError
from xml.parsers.expat import ExpatError


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
        
        if transcript == "API_ERROR":
            self.send_privmsg(
                message['command']['channel'], "Transcript could not be fetched, likely due to being rate limited. Please try again later.")
            return
            
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
        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        except (ParseError, ExpatError) as e:
            print(f"XML parsing error when listing transcripts for video {video_id}: {e}")
            return "API_ERROR"

        try:
            transcript = transcript_list.find_transcript(['en-GB'])
        except NoTranscriptFound:
            try:
                transcript = transcript_list.find_transcript(['en'])
            except NoTranscriptFound:
                for t in transcript_list:
                    try:
                        try:
                            transcript = t.translate('en')
                            break
                        except (ParseError, ExpatError) as e:
                            print(f"XML parsing error when translating for video {video_id}: {e}")
                            return "API_ERROR"
                    except Exception as e:
                        print(f"Translation error: {e}")
                        continue
                else:
                    return None

        # Fetch transcript without retrying
        try:
            fetched = transcript.fetch()
        except (ParseError, ExpatError) as e:
            print(f"XML parsing error when fetching transcript for video {video_id}: {e}")
            return "API_ERROR"
        
        # Check if fetched has a 'snippets' attribute, otherwise treat it as the transcript list directly
        if hasattr(fetched, 'snippets'):
            merged_text = " ".join(snippet.text.replace(r'\'', "'") for snippet in fetched.snippets)
        else:
            merged_text = " ".join(item['text'].replace(r'\'', "'") for item in fetched)
        
        return merged_text

    except (NoTranscriptFound, TranscriptsDisabled):
        print("Transcripts are disabled or none were found.")
        return None
    except (ParseError, ExpatError) as e:
        print(f"XML parsing error for video {video_id}: {e}")
        return "API_ERROR"
    except Exception as e:
        print(f"Unexpected error for video {video_id}: {e}")
        return None