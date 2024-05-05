import time

def reply_to_ping(bot, message):
    if (message.user not in bot.state or time.time() - bot.state[message.user] >
            bot.cooldown):
        bot.state[message.user] = time.time()
        
        # Measure the current time before sending the PONG message
        start_time = time.time()
        
        # Send the PONG message to acknowledge the PING
        bot.send_command('PONG :tmi.twitch.tv')
        
        # Calculate the latency time by subtracting the start time from the current time
        latency_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        text = f'@{message.user}, Pong! Latency: {latency_time:.2f} ms'
        bot.send_privmsg(message.channel, text)
