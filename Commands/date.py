import datetime
import time

def reply_with_date(bot, message):
    if (message['source']['nick'] not in bot.state or time.time() - bot.state[message['source']['nick']] >
            bot.cooldown):
        bot.state[message['source']['nick']] = time.time()
        formatted_date = datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')
        text = f"{message['source']['nick']}, the date is {formatted_date} EST."
        bot.send_privmsg(message['command']['channel'], text)

