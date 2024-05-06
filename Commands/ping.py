import time


def reply_to_ping(bot, message):
    if (message.user not in bot.state or time.time() - bot.state[message.user] >
            bot.cooldown):
        bot.state[message.user] = time.time()
        
        uptime_seconds = time.time() - bot.start_time
        uptime_hours = uptime_seconds // 3600
        uptime_minutes = (uptime_seconds % 3600) // 60
        uptime_seconds %= 60
        
        uptime_str = f"{int(uptime_hours)}h {int(uptime_minutes)}m {int(uptime_seconds)}s"
        
        response = f"@{message.user}, Pong! Uptime: {uptime_str}"
        bot.send_privmsg(message.channel, response)