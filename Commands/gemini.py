import time
from google import genai
from google.genai import types
import config

client = genai.Client(api_key=config.GOOGLE_API_KEY)

def reply_with_gemini(self, message):
    if (message['source']['nick'] not in self.state or time.time() - self.state[message['source']['nick']] >
            self.cooldown):
        self.state[message['source']['nick']] = time.time()

    if not message['command']['botCommandParams']:
        m = f"@{message['tags']['display-name']}, please provide a prompt for Gemini. Model: gemini-flash-lite-latest, \
            temperature: 1.1, top_p: 0.95"
        self.send_privmsg(message['command']['channel'], m)
        return

    prompt = (message['command']['botCommandParams'])
    result = generate(prompt)
    for m in result:
        self.send_privmsg(message['command']['channel'], m)
        time.sleep(1)


MODEL_NAME = "gemini-flash-lite-latest"
GENERATION_CONFIG = types.GenerateContentConfig(
    max_output_tokens=400,
    temperature=1.1,
    top_p=0.95,
    system_instruction=[types.Part.from_text(text="""Please always provide a short and concise response. Do not ask the user follow up questions, 
                        because you are intended to provide a single response with no history and are not expected
                        any follow up prompts. Answer should be at most 990 characters.""")]
)

def generate(prompt) -> list[str]:
    try:
        if isinstance(prompt, str):
            prompt = [prompt]
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=GENERATION_CONFIG
        ).text.replace('\n', ' ').replace('*', ' ')
        n = 495
        return [response[i:i+n] for i in range(0, len(response), n)]
    except Exception as e:
        print(e)
        return [f"Error: {str(e)}"]


def generate_emote_description(prompt):
    try:
        config = types.GenerateContentConfig(
            system_instruction=[types.Part.from_text(text="You don't need to say Here's a description, just say the result.")],
            max_output_tokens=400,
            temperature=1.1,
            top_p=0.95,
        )
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=config,
        ).text.replace('\n', ' ')
        response = response.replace('*', ' ')
        response = response.replace(r'\&', '&')
        return response
    except Exception as e:
        print(e)
        return None
