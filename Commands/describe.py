import requests
import time
import re
from google.genai import types
from Utils.utils import (
    fetch_cmd_data,
    check_cooldown,
    clean_str,
    send_chunks,
    gemini_generate,
    log_err
)

MODEL_NAME = "gemini-flash-lite-latest"
GENERATION_CONFIG = {
    "max_output_tokens": 400
}

# Maximum file size in bytes (1 GB)
MAX_FILE_SIZE = 1 * 1024 * 1024 * 1024
REQUEST_TIMEOUT_SECS = 30


def get_file_size(url):
    try:
        response = requests.head(url, timeout=REQUEST_TIMEOUT_SECS, allow_redirects=True)
        response.raise_for_status()
        content_length = response.headers.get('Content-Length')
        if content_length:
            return int(content_length)
    except Exception as e:
        print(f"Error fetching file size: {e}")
    return None


def get_content_type(url):
    try:
        # Try HEAD first
        response = requests.head(url, timeout=REQUEST_TIMEOUT_SECS, allow_redirects=True)
        response.raise_for_status()
        ctype = response.headers.get('Content-Type')
        if ctype:
            return ctype
        # Fallback to GET only if needed
        response = requests.get(url, stream=True, timeout=REQUEST_TIMEOUT_SECS)
        response.raise_for_status()
        return response.headers.get('Content-Type')
    except Exception as e:
        print(f"Error fetching content type: {e}")
        return None


def generate_gemini_description(media, input_text):
    if not media:
        return None
    return gemini_generate([media, input_text], MODEL_NAME, GENERATION_CONFIG)


def gemini_for_video(media, input_text):
    if not media:
        return None
    return gemini_generate([media, input_text], MODEL_NAME, GENERATION_CONFIG)


def upload_file_gemini(media_url, content_type):
    """Create a Part object for Gemini from media_url"""
    try:
        # Download the file
        response = requests.get(media_url, stream=True, timeout=REQUEST_TIMEOUT_SECS)
        response.raise_for_status()

        # Create inline data part
        file = types.Part.from_bytes(
            data=response.content,
            mime_type=content_type
        )
        return file
    except Exception as e:
        print(f"Error creating file part: {e}")
        return None


def reply_with_describe(self, message):
    cmd = fetch_cmd_data(self, message)

    if not check_cooldown(cmd.state, cmd.nick, cmd.cooldown):
        return

    if not cmd.params:
        m = f"{cmd.username}, please provide a link to an image, video, or emote name for Gemini to describe."
        self.send_privmsg(cmd.channel, m)
        return

    prompt = cmd.params.strip()
    channel_id = message["tags"]["room-id"]
    user_display_name = cmd.username

    # Check if the prompt is a URL
    if re.match(r'((ftp|http|https)://.+)|(\./frames/.+)', prompt):
        # Set media_url and content_type directly if prompt is a URL
        media_url = prompt
        content_type = get_content_type(media_url)
        print("Content type: ", content_type)
    else:
        # Check if the prompt is an emote name in the Emotes collection
        emote = self.db['Emotes'].find_one({"name": prompt})
        if emote:
            emote_id = emote['emote_id']
            is_global = emote.get("is_global", False)

            # Verify that the emote is either global or associated with the specified channel
            if is_global or self.db['ChannelEmotes'].find_one({"channel_id": channel_id, "emote_id": emote_id}):
                # Set image_url if emote is valid as global or channel-specific
                media_url = emote['url']
                content_type = get_content_type(media_url)
            else:
                m = f"{user_display_name}, the provided input is not a valid URL or available as a global/channel emote."
                self.send_privmsg(cmd.channel, m)
                return
        else:
            # Emote not found in the Emotes collection
            m = f"{user_display_name}, the provided input is not a valid URL or available as a global/channel emote."
            self.send_privmsg(cmd.channel, m)
            return

    description = None
    if content_type in ['image/jpeg', 'image/png', 'image/webp', 'image/gif']:
        try:
            image_file = upload_file_gemini(media_url, content_type)
            if not image_file:
                self.send_privmsg(cmd.channel, "Image could not be processed, check the link.")
                return
            time.sleep(1)
            input_text = "Give me a concise description of this image/gif, ideally under 100 words, translating to English if needed."
            print("Getting description...")
            description = generate_gemini_description(image_file, input_text)

        except Exception as e:
            log_err(e)
            self.send_privmsg(cmd.channel, "Image could not be processed, check the link.")
            return

    elif content_type in ['video/mp4']:
        try:
            file_size = get_file_size(media_url)
            if file_size and file_size > MAX_FILE_SIZE:
                m = f"{user_display_name}, the video is too large to process. Files are limited to 1 GB."
                self.send_privmsg(cmd.channel, m)
                return
            self.send_privmsg(cmd.channel, "Downloading video...")
            video_file = upload_file_gemini(media_url, content_type)
            if not video_file:
                self.send_privmsg(cmd.channel, "Video could not be downloaded, check the link.")
                return

            self.send_privmsg(cmd.channel, "Video is being uploaded to Gemini, please wait 5 seconds.")
            time.sleep(5)

            input_text = "Describe the content of this video, in under 100 words, translating to English if needed."
            description = gemini_for_video(video_file, input_text)

        except Exception as e:
            log_err(e)
            self.send_privmsg(cmd.channel, "Video could not be downloaded, check the link.")
            return

    elif content_type == 'application/pdf':
        try:
            self.send_privmsg(cmd.channel, "Document is being uploaded to Gemini, please wait 10 seconds.")
            pdf_file = upload_file_gemini(media_url, content_type)
            if not pdf_file:
                self.send_privmsg(cmd.channel, "PDF could not be processed.")
                return
            time.sleep(10)

            input_text = "Summarize this pdf, translating to English if needed."
            description = generate_gemini_description(pdf_file, input_text)

        except Exception as e:
            log_err(e)
            self.send_privmsg(cmd.channel, "PDF could not be processed.")
            return
    else:
        m = f"{user_display_name}, content type was found to be {content_type}. Please provide a valid emote name, or a link to an image or a .mp4 video."
        self.send_privmsg(cmd.channel, m)
        return

    if not description:
        self.send_privmsg(cmd.channel, "There was an error processing the content.")
        return

    clean_result = clean_str(description, ['`', '*'])
    send_chunks(self.send_privmsg, cmd.channel, clean_result)
