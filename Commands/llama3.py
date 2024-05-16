import time
import ollama

"""
Instructions:
Install ollama https://ollama.com/
pull llm u want to use
ollama pull gurubot/llama3-guru-uncensored

pip install ollama
"""


def reply_with_llama3(self, message):
    if (message.user not in self.state or time.time() - self.state[message.user] >
            self.cooldown):
        self.state[message.user] = time.time()

    if not message.text_args:
        m = f"@{message.user}, please provide a prompt. Model: llama3-uncensored, \
            https://ollama.com/gurubot/llama3-guru-uncensored"
        self.send_privmsg(message.channel, m)
        return

    prompt = ' '.join(message.text_args)
    self.send_privmsg(message.channel, "Result usually takes over a minute. Please wait.")
    result = generate(prompt)
    self.send_privmsg(message.channel, f"@{message.user},")
    time.sleep(1) 
    for m in result:
        self.send_privmsg(message.channel, m)
        time.sleep(1)


def generate(prompt):
    try:
        result = ollama.generate(model='mannix/llama3-uncensored', prompt=prompt, stream=False,
                                options= {"num_ctx": 1024})["response"]
        n = 495
        result = result.replace('\n', ' ')
        return [result[i:i+n] for i in range(0, len(result), n)]

    except Exception as e:
        print(e)
        return ["Some error occurred."]