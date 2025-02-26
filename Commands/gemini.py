import time
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import config
genai.configure(api_key=config.GOOGLE_API_KEY)

def reply_with_gemini(self, message):
    if (message['source']['nick'] not in self.state or time.time() - self.state[message['source']['nick']] >
            self.cooldown):
        self.state[message['source']['nick']] = time.time()

    if not message['command']['botCommandParams']:
        m = f"@{message['tags']['display-name']}, please provide a prompt for Gemini. Model: gemini-2.0-flash-lite-preview-02-05, \
            temperature: 1.1, top_p: 0.95"
        self.send_privmsg(message['command']['channel'], m)
        return

    prompt = (message['command']['botCommandParams'])
    result = generate(prompt)
    for m in result:
        self.send_privmsg(message['command']['channel'], m)
        time.sleep(1)


generation_config = {
    "max_output_tokens": 400,
    "temperature": 1.1,
    "top_p": 0.95,
}


safety_settings = {
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
}

system_instruction=["""Please always provide a short and concise response. Do not ask the user follow up questions, 
                        because you are intended to provide a single response with no history and are not expected
                        any follow up prompts. Answer should be at most 990 characters."""]


model = genai.GenerativeModel(
  model_name="gemini-2.0-flash-lite-preview-02-05",
  generation_config=generation_config,
  safety_settings=safety_settings,
  system_instruction=system_instruction
)

def generate(prompt) -> list[str]:
    try:
        if isinstance(prompt, str):
            prompt = [prompt]
        response = model.generate_content(
            prompt,
            stream=False,
        ).text.replace('\n', ' ')
        response = response.replace('*', ' ')
        n = 495
        return [response[i:i+n] for i in range(0, len(response), n)]
    except Exception as e:
        print(e)
        return ["Error: ", str(e[0:490])]


def generate_emote_description(prompt):
    system_instruction = [
        "You don't need to say Here's a description, just say the result."]
    try:
        model = genai.GenerativeModel(
            "gemini-2.0-flash-lite-preview-02-05",
            system_instruction=system_instruction
        )
        response = model.generate_content(
            prompt,
            generation_config=generation_config,
            safety_settings=safety_settings,
            stream=False,
        ).text.replace('\n', ' ')
        response = response.replace('*', ' ')
        return response
    except Exception as e:
        print(e)
        return None
