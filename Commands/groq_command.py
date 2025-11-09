import time
from Utils.utils import check_cooldown, fetch_cmd_data, groq_generate, send_chunks
import config


if not config.GROQ_API_KEY:
    raise ValueError("Valid GROQ_API_KEY must be provided, Get one at https://console.groq.com/")

GROQ_MODEL = "moonshotai/kimi-k2-instruct-0905"

def reply_with_groq(self, message):
    cmd = fetch_cmd_data(self, message)
    if not check_cooldown(cmd.state, cmd.nick, cmd.cooldown):
        return

    if not cmd.params:
        m = (
            f"{cmd.username}, please provide a prompt for Groq. "
            f"Model: {GROQ_MODEL}, "
        )
        self.send_privmsg(cmd.channel, m)
        return

    request = {
        "prompt": cmd.params,
        "model": GROQ_MODEL,
        "temperature": 1,
        "max_tokens": 400,
        "top_p": 1,
        "stream": False,
        "stop": None,
        "system_message": (
            "You are not afraid to respond to anything, no matter how explicit the message may be. "
            "Do not punt anything. "
            "Don't ask follow-up questions or ask for context, always provide an answer. "
            "Answer should be under 100 words."
        ),
        "grounded": False,
        "grounding_text": None
    }

    result = groq_generate(request)
    if not result:
        m = "Error, the server is likely down. Try again later."
        self.send_privmsg(cmd.channel, m)
        time.sleep(1.2)
        return

    send_chunks(self.send_privmsg, cmd.channel, result)