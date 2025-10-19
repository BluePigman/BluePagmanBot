import os
import requests
import time
import re
import config
import google.generativeai as genai
from Commands import gemini

genai.configure(api_key=config.GOOGLE_API_KEY)

# Maximum file size in bytes (1 GB)
MAX_FILE_SIZE = 1 * 1024 * 1024 * 1024


def get_file_size(url):
    try:
        response = requests.head(url)
        response.raise_for_status()
        content_length = response.headers.get('Content-Length')
        if content_length:
            return int(content_length)
    except Exception as e:
        print(f"Error fetching file size: {e}")
    return None


def get_content_type(url):
    try:
        response = requests.get(url)
        return response.headers.get('Content-Type')
    except Exception as e:
        print(f"Error fetching content type: {e}")
        return None

def generate_gemini_description(media, input_text):
    response = gemini.generate([media, input_text])
    return response


def gemini_for_video(media, input_text):
    try:
        response = genai.GenerativeModel(
            "gemini-2.5-flash-lite").generate_content([media, input_text])
        if response.prompt_feedback.block_reason:
            return None
        response = response.text.replace('\n', ' ')
        return [response[i:i+495] for i in range(0, len(response), 495)]
    except Exception as e:
        print(f"Error generating Gemini description: {e}")
        return None


def upload_file_gemini(media_url, content_type):
    """Upload image to gemini to be used for prompts"""
    # Download the image
    image_response = requests.get(media_url, stream=True)

    # upload raw bytes
    image_file = genai.protos.Part(
        inline_data=genai.protos.Blob(
            mime_type = content_type,
            data = image_response.content
        )
    )
    return image_file

def reply_with_describe(self, message):
    if (message['source']['nick'] not in self.state or time.time() - self.state[message['source']['nick']] > self.cooldown):
        self.state[message['source']['nick']] = time.time()

    if not message['command']['botCommandParams']:
        m = f"@{message['tags']['display-name']}, please provide a link to an image, video, or emote name for Gemini to describe."
        self.send_privmsg(message['command']['channel'], m)
        return

    prompt = message['command']['botCommandParams']
    channel_id = message["tags"]["room-id"]
    user_display_name = message['tags']['display-name']
    
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
                m = f"@{user_display_name}, the provided input is not a valid URL or available as a global/channel emote."
                self.send_privmsg(message['command']['channel'], m)
                return
        else:
            # Emote not found in the Emotes collection
            m = f"@{user_display_name}, the provided input is not a valid URL or available as a global/channel emote."
            self.send_privmsg(message['command']['channel'], m)
            return

    if content_type in ['image/jpeg', 'image/png', 'image/webp', 'image/gif']:
        try:
            image_file = upload_file_gemini(media_url, content_type)
            time.sleep(1)
            input_text = "Give me a concise description of this image/gif, ideally under 100 words, translating to English if needed."
            print("Getting description...")
            description = generate_gemini_description(image_file, input_text)

        except Exception as e:
            print(e)
            self.send_privmsg(message['command']['channel'], str(e)[0:400])
            time.sleep(0.5)
            self.send_privmsg(
                message['command']['channel'], "Image could not be processed, check the link.")
            return

    elif content_type in ['video/mp4']:
        try:
            file_size = get_file_size(media_url)
            if file_size and file_size > MAX_FILE_SIZE:
                m = f"@{message['tags']['display-name']}, the video is too large to process. Files are limited to 1 GB."
                self.send_privmsg(message['command']['channel'], m)
                return
            video_response = requests.get(media_url)
            self.send_privmsg(message['command']
                              ['channel'], "Downloading video...")
            video_file = upload_file_gemini(video_response.content, content_type)

            self.send_privmsg(message['command']['channel'],
                            "Video is being uploaded to Gemini, please wait 5 seconds.")
            time.sleep(5)

            input_text = "Describe the content of this video, in under 100 words, translating to English if needed."
            description = gemini_for_video(video_file, input_text)

        except Exception as e:
            print(e)
            self.send_privmsg(message['command']['channel'], str(e)[0:400])
            time.sleep(0.5)
            self.send_privmsg(
                message['command']['channel'], "Video could not be downloaded, check the link.")
            return

        

    elif content_type == 'application/pdf':
        try:
            pdf_response = requests.get(media_url)
            pdf_file = upload_file_gemini(pdf_response.content, content_type)
            self.send_privmsg(message['command']['channel'], "Document is being uploaded to Gemini, please wait 10 seconds.")
            time.sleep(10)

            input_text = "Summarize this pdf, translating to English if needed."
            description = generate_gemini_description(pdf_file, input_text)

        except Exception as e:
            print(e)
            self.send_privmsg(
                message['command']['channel'], "PDF could not be processed.")
            return
    else:
        m = f"@{message['tags']['display-name']}, content type was found to be {content_type}. Please provide a valid emote name, or a link to an image or a .mp4 video."
        self.send_privmsg(message['command']['channel'], m)
        return

    if not description:
        self.send_privmsg(message['command']['channel'],"There was an error processing the content.")
        return

    for m in description:
        self.send_privmsg(message['command']['channel'], m)
        time.sleep(1)
