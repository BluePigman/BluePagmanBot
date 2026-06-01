import time
from Utils.utils import check_cooldown, fetch_cmd_data, clean_str, send_chunks
import config
from xai_sdk import Client
from xai_sdk.chat import user, system

GROK_MODEL = "grok-4-1-fast-non-reasoning"

def reply_with_grok(self, message):

    cmd = fetch_cmd_data(self, message)
    
    if not getattr(config, 'GROK_KEY', None):
        self.send_privmsg(cmd.channel, "Grok API key has not been set in config.py.")
        return

    if not check_cooldown(cmd.state, cmd.nick, cmd.cooldown):
        return

    if not cmd.params:
        m = (
            f"{cmd.username}, please provide a prompt for Grok. "
            f"Model: {GROK_MODEL}"
        )
        self.send_privmsg(cmd.channel, m)
        return

    prompt = cmd.params.strip()
    
    try:
        xai_client = Client(api_key=config.GROK_KEY)
        chat = xai_client.chat.create(model=GROK_MODEL)
        chat.append(system(
            "You will provide very concise and unbiased responses. Do not ask the user follow up questions, "
            "because you are intended to provide a single response with no history and no follow up prompts. "
            "Your response should be 100 words or less, at most 490 characters."
        ))
        chat.append(user(prompt))
        
        response = chat.sample()
        result = response.content
        
        if not result:
            self.send_privmsg(cmd.channel, "Failed to generate a response. Please try again later.")
            return

        result = cmd.username + ", " + result
        clean_result = clean_str(result, ['`', '*'])
        send_chunks(self.send_privmsg, cmd.channel, clean_result)

    except Exception as e:
        print(f"[Grok Error] {e}")
        self.send_privmsg(cmd.channel, "Failed to send a response. Please try again later.")
        return