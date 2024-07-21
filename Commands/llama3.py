import time
import ollama

"""
Instructions:
Install ollama https://ollama.com/
pull llm u want to use
ollama pull dolphin-llama3:8b

pip install ollama
"""


def reply_with_llama3(self, message):
    if (message['source']['nick'] not in self.state or time.time() - self.state[message['source']['nick']] >
            self.cooldown):
        self.state[message['source']['nick']] = time.time()

    if not message['command']['botCommandParams']:
        m = f"@{message['tags']['display-name']}, please provide a prompt. Model: Dolphin 2.9 Llama 3, \
            https://ollama.com/library/dolphin-llama3"
        self.send_privmsg(message['command']['channel'], m)
        return

    prompt = message['command']['botCommandParams']
    self.send_privmsg(message['command']['channel'], "Result usually takes a few minutes. Please wait.")
    result = generate(prompt)
    self.send_privmsg(message['command']['channel'], f"@{message['tags']['display-name']},")
    time.sleep(1) 
    for m in result:
        self.send_privmsg(message['command']['channel'], m)
        time.sleep(1)


def generate(prompt):
    try:
        result = ollama.generate(model='dolphin-llama3', prompt=prompt, stream=False,
                                options= {"num_ctx": 1024})["response"]
        n = 495
        result = result.replace('\n', ' ')
        result = result.replace('\r\n', ' ')
        return [result[i:i+n] for i in range(0, len(result), n)]

    except Exception as e:
        print(e)
        return ["Some error occurred."]