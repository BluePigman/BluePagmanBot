import random
import time

responses = [
    "😃 It is certain.",
    "😃 It is decidedly so.",
    "😃 Without a doubt.",
    "😃 Yes - definitely.",
    "😃 You may rely on it.",
    "😃 As I see it, yes.",
    "😃 Most likely.",
    "😃 Outlook good.",
    "😃 Yes.",
    "😃 Signs point to yes.",
    "😐 Reply hazy, try again.",
    "😐 Ask again later.",
    "😐 Better not tell you now.",
    "😐 Cannot predict now.",
    "😐 Concentrate and ask again.",
    "😦 Don't count on it.",
    "😦 My reply is no.",
    "😦 My sources say no.",
    "😦 Outlook not so good.",
    "😦 Very doubtful."
]


def reply_with_eight_ball(self, message):
    if message['source']['nick'] not in self.state or time.time() - self.state[message['source']['nick']] > self.cooldown:
        self.state[message['source']['nick']] = time.time()

        if message['command']['botCommandParams']:  # Check if a question was asked
            response = random.choice(responses)
            self.send_privmsg(
                message['command']['channel'], f"@{message['tags']['display-name']}, {response}")
        else:
            self.send_privmsg(
                message['command']['channel'], f"@{message['tags']['display-name']}, please ask a question.")
