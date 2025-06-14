import random
from Utils.utils import check_cooldown, fetch_cmd_data

responses = [
    "😃 It is certain.",
    "😃 It is decidedly so.",
    "😃 Without a doubt.",
    "😃 Yes - definitely.",
    "😃 You may rely on it.",
    "😃 As I see it, yes.",
    "😃 Most likely.",
    "😃 Outlook good.",
    "😃 Yes ",
    "😃 Signs point to yes.",
    "😐 Reply hazy, try again.",
    "😐 Ask again later.",
    "😐 Better not tell you now.",
    "😐 Cannot predict now.",
    "😐 Concentrate and ask again.",
    "😦 Don't count on it.",
    "😦 My reply is No",
    "😦 My sources say No",
    "😦 Outlook not so good.",
    "😦 Very doubtful."
]


def reply_with_eight_ball(self, message):
    cmd = fetch_cmd_data(self, message)
    if not check_cooldown(cmd.state, cmd.nick, cmd.cooldown): 
        return

    response = random.choice(responses)
    self.send_privmsg(cmd.channel, f"{cmd.username}, {response}")