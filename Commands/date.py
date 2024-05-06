import datetime
import time

def reply_with_date(bot, message):
    if (message.user not in bot.state or time.time() - bot.state[message.user] >
            bot.cooldown):
        bot.state[message.user] = time.time()
        formatted_date = datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')
        text = f'{message.user}, the date is {formatted_date} EST.'
        bot.send_privmsg(message.channel, text)

