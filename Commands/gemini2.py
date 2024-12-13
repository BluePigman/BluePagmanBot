import time
import vertexai
from vertexai.generative_models import GenerativeModel, SafetySetting, Tool, grounding


def reply_with_gemini_experimental(self, message):
    if (message['source']['nick'] not in self.state or time.time() - self.state[message['source']['nick']] >
            self.cooldown):
        self.state[message['source']['nick']] = time.time()

    if not message['command']['botCommandParams']:
        m = f"@{message['tags']['display-name']}, please provide a prompt for Gemini. Model: gemini-2.0-flash-exp, \
            temperature: 2, top_p: 0.75"
        self.send_privmsg(message['command']['channel'], m)
        return

    prompt = message['command']['botCommandParams']
    result = generate(prompt)
    for m in result:
        self.send_privmsg(message['command']['channel'], m)
        time.sleep(1.5)


generation_config = {
    "max_output_tokens": 400,
    "temperature": 2,
    "top_p": 0.75,
}

safety_settings = [
    SafetySetting(
        category=SafetySetting.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
        threshold=SafetySetting.HarmBlockThreshold.BLOCK_NONE
    ),
    SafetySetting(
        category=SafetySetting.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
        threshold=SafetySetting.HarmBlockThreshold.BLOCK_NONE
    ),
    SafetySetting(
        category=SafetySetting.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
        threshold=SafetySetting.HarmBlockThreshold.BLOCK_NONE
    ),
    SafetySetting(
        category=SafetySetting.HarmCategory.HARM_CATEGORY_HARASSMENT,
        threshold=SafetySetting.HarmBlockThreshold.BLOCK_NONE
    ),
]

# tools = [
#     Tool.from_google_search_retrieval(
#         google_search_retrieval=grounding.GoogleSearchRetrieval()
#     ),
# ]


def generate(prompt) -> list[str]:
    vertexai.init(project="bluepagmanbot", location="us-central1")
    model = GenerativeModel(
        "gemini-2.0-flash-exp",
        # tools=tools,
        system_instruction=["""Please always provide a short and concise response. Do not ask the user follow up questions, 
                        because you are intended to provide a single response with no history and are not expected
                        any follow up prompts. If given a media file, please describe it. For GIFS/WEBP files describe all frames.
                        Answer should be at most 990 characters. Don't mention source numbers because the user
                            will not know what they are referring to."""]
    )
    try:
        if isinstance(prompt, str):
            prompt = [prompt]

        response = model.generate_content(
            prompt,
            generation_config=generation_config,
            safety_settings=safety_settings,
            stream=False,
        ).text.replace('\n', ' ')
        response = response.replace('*', ' ')
        n = 495
        return [response[i:i+n] for i in range(0, len(response), n)]
    except Exception as e:
        print(e)
        return ["Error: ", e[0:490]]
