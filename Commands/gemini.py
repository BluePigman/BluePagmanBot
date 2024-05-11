import time

import vertexai
from vertexai.generative_models import GenerativeModel
import vertexai.preview.generative_models as generative_models


def reply_with_gemini(self, message):
    if (message.user not in self.state or time.time() - self.state[message.user] >
            self.cooldown):
        self.state[message.user] = time.time()

    if not message.text_args:
        m = f"@{message.user}, please provide a prompt for Gemini. Model: gemini-1.5-pro-preview-0409, \
            temperature: 1.5, top_p: 0.95"
        self.send_privmsg(message.channel, m)
        return

    prompt = ' '.join(message.text_args)
    result = generate(prompt)
    for m in result:
        self.send_privmsg(message.channel, m)
        time.sleep(1)



generation_config = {
    "max_output_tokens": 400,
    "temperature": 1.1,
    "top_p": 0.95,
}

safety_settings = {
    generative_models.HarmCategory.HARM_CATEGORY_HATE_SPEECH: generative_models.HarmBlockThreshold.BLOCK_NONE,
    generative_models.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: generative_models.HarmBlockThreshold.BLOCK_NONE,
    generative_models.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: generative_models.HarmBlockThreshold.BLOCK_NONE,
    generative_models.HarmCategory.HARM_CATEGORY_HARASSMENT: generative_models.HarmBlockThreshold.BLOCK_NONE,
}

def generate(prompt):
    vertexai.init(project="bluepagmanbot", location="us-east1")
    model = GenerativeModel(
    "gemini-1.5-pro-preview-0409",
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


