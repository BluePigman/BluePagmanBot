import time

import vertexai
from vertexai.generative_models import GenerativeModel
import vertexai.preview.generative_models as generative_models


def reply_with_gemini(self, message):
    if (message['source']['nick'] not in self.state or time.time() - self.state[message['source']['nick']] >
            self.cooldown):
        self.state[message['source']['nick']] = time.time()

    if not message['command']['botCommandParams']:
        m = f"@{message['tags']['display-name']}, please provide a prompt for Gemini. Model: gemini-1.5-flash-001, \
            temperature: 1.1, top_p: 0.95"
        self.send_privmsg(message['command']['channel'], m)
        return

    prompt = (message['command']['botCommandParams'])
    result = generate(prompt)
    for m in result:
        self.send_privmsg(message['command']['channel'], m)
        time.sleep(1)



generation_config = {
    "max_output_tokens": 2000,
    "temperature": 1.1,
    "top_p": 0.95,
}

safety_settings = {
    generative_models.HarmCategory.HARM_CATEGORY_HATE_SPEECH: generative_models.HarmBlockThreshold.BLOCK_ONLY_HIGH,
    generative_models.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: generative_models.HarmBlockThreshold.BLOCK_ONLY_HIGH,
    generative_models.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: generative_models.HarmBlockThreshold.BLOCK_ONLY_HIGH,
    generative_models.HarmCategory.HARM_CATEGORY_HARASSMENT: generative_models.HarmBlockThreshold.BLOCK_ONLY_HIGH,
}

def generate(prompt):
    vertexai.init(project="bluepagmanbot", location="us-central1")
    model = GenerativeModel(
    "gemini-1.5-flash-001",
    system_instruction=["Please always provide a complete response. Make up an answer if you do not have enough \
                        information or context regarding the prompt. Do not ask the user follow up questions, \
                        because you are intended to provide a single response with no history and are not expected \
                        any follow up prompts."]
    )
    try:
        response = model.generate_content(
            [prompt],
            generation_config=generation_config,
            safety_settings=safety_settings,
            stream=False,
        ).text.replace('\n', ' ')
        response = response.replace('*', ' ')
        n = 495
        return [response[i:i+n] for i in range(0, len(response), n)]
    except Exception as e:
        print(e)
        return ["Error: prompt was likely blocked."]


