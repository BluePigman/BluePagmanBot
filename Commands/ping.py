import time
from Utils.utils import check_cooldown, fetch_cmd_data


def calculate_uptime(bot):
    uptime_seconds = time.time() - bot.start_time
    uptime_hours = uptime_seconds // 3600
    uptime_minutes = (uptime_seconds % 3600) // 60
    uptime_seconds %= 60
    return f"{int(uptime_hours)}h, {int(uptime_minutes)}m, {int(uptime_seconds)}s"


def reply_to_ping(self, message):
    cmd = fetch_cmd_data(self, message)
    if not check_cooldown(cmd.state, cmd.nick, cmd.cooldown): 
        return

    uptime_str = calculate_uptime(self)

    # Calculate latency from Twitch's message timestamp
    tags = message.get('tags') or {}
    sent_ts = tags.get('tmi-sent-ts')

    if sent_ts:
        try:
            latency_time = (time.time() * 1000) - float(sent_ts)
            text = f"{cmd.username}, Pong! Latency: {latency_time:.2f} ms | Uptime: {uptime_str}"
        except (ValueError, TypeError):
            text = f"{cmd.username}, Pong! | Uptime: {uptime_str}"
    else:
        text = f"{cmd.username}, Pong! | Uptime: {uptime_str}"

    self.send_privmsg(cmd.channel, text)