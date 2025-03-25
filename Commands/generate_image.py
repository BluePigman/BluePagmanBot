import time
from google import genai
from google.genai import types
import requests
from config import GOOGLE_API_KEY



def reply_with_generate(self, message):
    if (message['source']['nick'] not in self.state or time.time() - self.state[message['source']['nick']] >
            self.cooldown):

        if not message['command']['botCommandParams']:
            m = f"@{message['tags']['display-name']}, please provide a prompt for Gemini Image generation Model: gemini-2.0-flash-exp-image-generation."
            self.send_privmsg(message['command']['channel'], m)
            return
        
        self.state[message['source']['nick']] = time.time()
        prompt = message['command']['botCommandParams']
        result = generate_image(f"Generate an image of {prompt}. If prompt is unclear then the interpretation is up to you, be creative. Always generate an image, don't ask any clarifying questions.")
        
        self.send_privmsg(message['command']['channel'], f"@{message['tags']['display-name']}, {result}")




def generate_image(prompt) -> str:
    client = genai.Client(api_key=GOOGLE_API_KEY)
    model = "gemini-2.0-flash-exp-image-generation"
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=prompt),
            ],
        )
    ]
    generate_content_config = types.GenerateContentConfig(
        temperature=1,
        top_p=0.95,
        top_k=40,
        max_output_tokens=8192,
        response_modalities=[
            "image",
            "text",
        ],
        safety_settings=[
            types.SafetySetting(
                category="HARM_CATEGORY_CIVIC_INTEGRITY",
                threshold="OFF",  # Off
            ),
        ],
        response_mime_type="text/plain",
    )
    


    for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
    ):
        if not chunk.candidates or not chunk.candidates[0].content or not chunk.candidates[0].content.parts:
            return "Image was not generated. Please try again."
        if chunk.candidates[0].content.parts[0].inline_data:
            inline_data = chunk.candidates[0].content.parts[0].inline_data
            files = {
                'file': inline_data.data # bytestring
            }
            response = requests.post('https://kappa.lol/api/upload',files=files)
            time.sleep(1)
            response = response.json()
            try:
                if response["link"]:
                    return response["link"]
            except Exception as e:
                return str(e)[:490]
        else:
            return "The prompt was blocked, please try again."
