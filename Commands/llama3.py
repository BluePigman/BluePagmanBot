import time

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

        self.send_privmsg(message['command']['channel'], "The Llama command has been removed.")