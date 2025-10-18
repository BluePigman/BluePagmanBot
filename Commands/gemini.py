import time
import google.generativeai as genai
import config
genai.configure(api_key=config.GOOGLE_API_KEY)

def reply_with_gemini(self, message):
    if (message['source']['nick'] not in self.state or time.time() - self.state[message['source']['nick']] >
            self.cooldown):
        self.state[message['source']['nick']] = time.time()

    if not message['command']['botCommandParams']:
        m = f"@{message['tags']['display-name']}, please provide a prompt for Gemini. Model: gemini-2.5-flash-lite, \
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

system_instruction=["""Please always provide a short and concise response. Do not ask the user follow up questions, 
                        because you are intended to provide a single response with no history and are not expected
                        any follow up prompts. Answer should be at most 990 characters."""]

model = genai.GenerativeModel(
  model_name="gemini-2.5-flash-lite",
  generation_config=generation_config,
  system_instruction=system_instruction
)

def generate(prompt) -> list[str]:
    try:
        if isinstance(prompt, str):
            prompt = [prompt]
        response = model.generate_content(
            prompt,
            stream=False,
        ).text.replace('\n', ' ').replace('*', ' ')
        n = 495
        return [response[i:i+n] for i in range(0, len(response), n)]
    except Exception as e:
        print(e)
        return [f"Error: {str(e)}"]


def generate_emote_description(prompt):
    system_instruction = [
        "You don't need to say Here's a description, just say the result."]
    try:
        model = genai.GenerativeModel(
            "gemini-2.0-flash",
            system_instruction=system_instruction
        )
        response = model.generate_content(
            prompt,
            generation_config=generation_config,
            stream=False,
        ).text.replace('\n', ' ')
        response = response.replace('*', ' ')
        response = response.replace(r'\&', '&')
        return response
    except Exception as e:
        print(e)
        return None
