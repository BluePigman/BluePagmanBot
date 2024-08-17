import re, time
from Commands import gemini
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound


def reply_with_summarize(self, message):
    if (message['source']['nick'] not in self.state or time.time() - self.state[message['source']['nick']] >
            self.cooldown):
        self.state[message['source']['nick']] = time.time()

    if not message['command']['botCommandParams']:
        m = f"@{message['tags']['display-name']}, please provide a prompt for Gemini. Model: gemini-1.5-flash-001, \
            temperature: 1.1, top_p: 0.95"
        self.send_privmsg(message['command']['channel'], m)
        return

    prompt = (message['command']['botCommandParams'])
    if "youtube.com" in prompt or "youtu.be" in prompt:
        video_id = extract_youtube_id(prompt)
        if not video_id:
            self.send_privmsg(message['command']['channel'], "Youtube vid not found.")
            return
        transcript = get_transcript(video_id)
        if not transcript:
            self.send_privmsg(message['command']['channel'], "No transcript found for the video.")
            return
        prompt = f"Here is the transcript for a youtube video, please summarize it in under 500 characters, \
        ignoring any sponsors of the video: {transcript}"
    else:
        self.send_privmsg(message['command']['channel'], "Please provide a Youtube link to summarize.")
        return
    result = gemini.generate(prompt)
    for m in result:
        self.send_privmsg(message['command']['channel'], m)
        time.sleep(1)

def extract_youtube_id(text):
    # Regular expression to match standard and shortened YouTube URLs
    youtube_regex = r"(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+$"
    
    # Check if the text contains a YouTube link
    match = re.search(youtube_regex, text)
    if match:
        # For standard YouTube URLs
        if "youtube.com" in text:
            video_id = text.split("v=")[-1].split("&")[0]
        # For shortened YouTube URLs
        elif "youtu.be" in text:
            video_id = text.split("/")[-1].split("?")[0]
        return video_id
    else:
        return None

def get_transcript(video_id):
    try:
        # First, try to get the manually created English transcript
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en-GB', 'en'])
    except NoTranscriptFound:
        try:
            # If not available, try to get the auto-generated English transcript
            transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
        except NoTranscriptFound:
            try:
                # If no English transcript is available, get any available transcript and translate it to English
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                
                for transcript in transcript_list:
                    try:
                        # Attempt to fetch and translate the first available transcript to English
                        transcript = transcript.translate('en').fetch()
                        break
                    except:
                        continue
                else:
                    # If no transcript could be translated, raise an exception
                    raise NoTranscriptFound(video_id)
            except NoTranscriptFound:
                return None
    except TranscriptsDisabled:
        return None

    # Merge all text into a single string and remove newline characters
    merged_text = " ".join([item['text'].replace('\n', ' ') for item in transcript])
    return merged_text