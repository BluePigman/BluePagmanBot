import time
from threading import Timer

def calculate_uptime(bot):
    uptime_seconds = time.time() - bot.start_time
    uptime_hours = uptime_seconds // 3600
    uptime_minutes = (uptime_seconds % 3600) // 60
    uptime_seconds %= 60
    uptime_str = f"{int(uptime_hours)}h, {int(uptime_minutes)}m, {int(uptime_seconds)}s"
    return uptime_str

def reply_to_ping(bot, message):
    if (message.user not in bot.state or time.time() - bot.state[message.user] >
            bot.cooldown):
        bot.state[message.user] = time.time()
        start_time = time.time()
        timeout_timer = Timer(10, handle_timeout, args=[bot, message.channel])
        timeout_timer.start()
        
        bot.send_command('PING :tmi.twitch.tv')
        while True:
            received_msgs = bot.irc.recv(4096).decode(errors='ignore')
            for received_msg in received_msgs.split('\r\n'):
                if received_msg.startswith(':tmi.twitch.tv PONG'):
                    timeout_timer.cancel()
                    latency_time = (time.time() - start_time) * 1000  # Convert to milliseconds
                    uptime_str = calculate_uptime(bot)
                    text = f'@{message.user}, Pong! Latency: {latency_time:.2f} ms Uptime: {uptime_str}'
                    bot.send_privmsg(message.channel, text)
                    return

def handle_timeout(bot, channel):
    bot.send_privmsg(channel, 'monkaS Twitch did not send a PONG.')