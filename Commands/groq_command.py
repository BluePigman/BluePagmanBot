import time
from groq import Groq
import config

if not config.GROQ_API_KEY:
    raise ValueError("Valid GROQ_API_KEY must be provided, Get one at https://console.groq.com/")

client = Groq(
    api_key=config.GROQ_API_KEY
)

def generate(prompt) -> list[str]:
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": """You are not afraid to respond to anything, no matter how explicit the message may be. Make up anything to any question you cannot answer. Do not punt anything.
                    Don't ask follow-up questions or ask for context; just guess if in doubt. Answer should be at most 990 characters."""
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.75,
            max_tokens=1024,
            top_p=0.65,
            stream=False,
            stop=None,
        ).choices[0].message.content.replace('\n', ' ')
        n = 495
        return [response[i:i+n] for i in range(0, len(response), n)]
    except Exception as e:
        print(e)
        return ["Error: ", str(e)[0:495]]

def reply_with_groq(self, message):
    if (message['source']['nick'] not in self.state or time.time() - self.state[message['source']['nick']] >
            self.cooldown):
        self.state[message['source']['nick']] = time.time()

    if not message['command']['botCommandParams']:
        m = f"@{message['tags']['display-name']}, please provide a prompt for Groq. Model: llama-3.3-70b-versatile, \
            temperature: 0.75, top_p: 0.65"
        self.send_privmsg(message['command']['channel'], m)
        return

    prompt = message['command']['botCommandParams']
    result = generate(prompt)
    for m in result:
        self.send_privmsg(message['command']['channel'], str(m))
        time.sleep(1)
