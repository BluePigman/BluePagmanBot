import base64
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
        result = generate_image(prompt)
        
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
        response_modalities=[
            "image",
            "text",
        ],
        response_mime_type="text/plain",
    )

    try:
        for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
        ):
            if (
                chunk.candidates is None
                or chunk.candidates[0].content is None
                or chunk.candidates[0].content.parts is None
                or chunk.candidates[0].content.parts[0].inline_data is None
            ):
                continue
            
            inline_data = chunk.candidates[0].content.parts[0].inline_data
            image_bytes = base64.b64decode(inline_data.data) if inline_data.data.startswith(b'iVBORw') else inline_data.data
            files = {
                'file': ('generated_image' + ".png", image_bytes, "image/png")
            }

            try:
                response = requests.post('https://kappa.lol/api/upload',files=files).json()
                if response["link"]:
                    return response["link"]
            except Exception as e:
                print(e)
                return f"Error, {str(e)}"
        
        return "Image could not be generated."
                
    except Exception as e:
        print(e)
        return "Error, the prompt was likely blocked."