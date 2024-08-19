import os, requests, time, re, config
from PIL import Image
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

genai.configure(api_key=config.GOOGLE_API_KEY)

safety_settings = {
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE
}

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

def reply_with_describe(self, message):
    if (message['source']['nick'] not in self.state or time.time() - self.state[message['source']['nick']] > self.cooldown):
        self.state[message['source']['nick']] = time.time()

    if not message['command']['botCommandParams']:
        m = f"@{message['tags']['display-name']}, please provide a link to an image or video for Gemini to describe."
        self.send_privmsg(message['command']['channel'], m)
        return

    prompt = message['command']['botCommandParams']

    # Regex to check if the URL is for an image or video
    if re.match(r'((ftp|http|https)://.+)|(\./frames/.+)', prompt):
        media_url = prompt
        try:
            if any(ext in media_url.lower() for ext in ['.jpg', '.jpeg', '.png', 'format=jpg', 'cdn.']):
                try:
                    image = Image.open(requests.get(media_url, stream=True).raw)
                    response = genai.GenerativeModel("gemini-1.5-flash", safety_settings=safety_settings).generate_content(["Give me a concise description of this image, ideally under 100 words.", image])
                    description = response.text.replace('\n', ' ')
                except Exception as e:
                    print(e)
                    self.send_privmsg(message['command']['channel'], "Image could not be processed, check the link.")
                    return
            
            elif '.mp4' in media_url.lower():
                try:
                    file_size = get_file_size(media_url)
                    if file_size and file_size > MAX_FILE_SIZE:
                        m = f"@{message['tags']['display-name']}, the video is too large to process. Files are limited to 1 GB."
                        self.send_privmsg(message['command']['channel'], m)
                        return
                    video_response = requests.get(media_url)
                    self.send_privmsg(message['command']['channel'], "Downloading video...")
                    
                except Exception as e:
                    print(e)
                    self.send_privmsg(message['command']['channel'], "Video could not be downloaded, check the link.")
                    return

                # Save video to a temporary file
                video_file_name = "temp_video.mp4"
                with open(video_file_name, 'wb') as video_file:
                    video_file.write(video_response.content)

                video_file = genai.upload_file(video_file_name, mime_type="video/mp4")
                self.send_privmsg(message['command']['channel'], "Video is being uploaded to Gemini, please wait 10 seconds.")
                time.sleep(10) 
                
                response = genai.GenerativeModel("gemini-1.5-flash", safety_settings=safety_settings).generate_content([video_file, "Describe the content of this video, in under 100 words, translating to English if needed."])
                description = response.text.replace('\n', ' ')

                os.remove(video_file_name)

            else:
                m = f"@{message['tags']['display-name']}, unsupported media type. Please provide a link to an image or a .mp4 video."
                self.send_privmsg(message['command']['channel'], m)
                return
            
            n = 495
            result = [description[i:i+n] for i in range(0, len(description), n)]
            
            for m in result:
                self.send_privmsg(message['command']['channel'], m)
                time.sleep(1)
        except Exception as e:
            print(e)
            error_message = f"Error: prompt was likely blocked or there was an issue processing the media."
            self.send_privmsg(message['command']['channel'], error_message)
    else:
        m = f"@{message['tags']['display-name']}, the provided input is not a valid URL."
        self.send_privmsg(message['command']['channel'], m)
