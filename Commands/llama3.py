import time
import ollama
import asyncio
"""
Instructions:
Install ollama https://ollama.com/
pull llm u want to use
ollama pull dolphin-llama3:8b

pip install ollama
"""


async def reply_with_llama3(self, message):
    if (message.user not in self.state or time.time() - self.state[message.user] >
            self.cooldown):
        self.state[message.user] = time.time()

    if not message.text_args:
        m = f"@{message.user}, please provide a prompt. Model: Dolphin 2.9 Llama 3, \
            https://ollama.com/library/dolphin-llama3"
        await self.send_privmsg(message.channel, m)
        return

    prompt = ' '.join(message.text_args)
    await self.send_privmsg(message.channel, "Result usually takes a few minutes. Please wait.")
    result = await generate(prompt)
    await self.send_privmsg(message.channel, f"@{message.user},")
    await asyncio.sleep(1) 
    for m in result:
        await self.send_privmsg(message.channel, m)
        await asyncio.sleep(1)


async def generate(prompt):
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