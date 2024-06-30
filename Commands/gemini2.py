import time

import vertexai
from vertexai.generative_models import GenerativeModel
import vertexai.preview.generative_models as generative_models


def reply_with_gemini_experimental(self, message):
    if (message['source']['nick'] not in self.state or time.time() - self.state[message['source']['nick']] >
            self.cooldown):
        self.state[message['source']['nick']] = time.time()

    if not message['command']['botCommandParams']:
        m = f"@{message['source']['nick']}, please provide a prompt for Gemini. Model: gemini-experimental, \
            temperature: 2"
        self.send_privmsg(message['command']['channel'], m)
        return

    prompt = ' '.join(message['command']['botCommandParams'])
    result = generate(prompt)
    for m in result:
        self.send_privmsg(message['command']['channel'], m)
        time.sleep(1)



generation_config = {
    "max_output_tokens": 300,
    "temperature": 2,
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
    "gemini-experimental",
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
        return ["Error: prompt was likely blocked."]
