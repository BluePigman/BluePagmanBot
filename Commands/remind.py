import time
import threading
from datetime import datetime, timedelta
from reminder_class import Reminder


def reply_with_reminder(self, message):
    user = message['tags']['display-name']
    channel = message['command']['channel']

    # Enforce cooldown
    if user not in self.state or time.time() - self.state[user] > self.cooldown:
        self.state[user] = time.time()

        # Parse command parameters
        recipient, time_str, reminder_message = parse_remind_command(
            message['command']['botCommandParams'])

        # Check if time_str is missing or invalid
        if time_str is None:
            self.send_privmsg(
                channel, f"@{user}, please specify a valid time for the reminder, like 'in 30s' or 'in 2h'.")
            return

        # Parse time string to seconds
        seconds = parse_time_to_seconds(time_str)
        if seconds is None:
            self.send_privmsg(
                channel, f"@{user}, invalid time format or time is too large. Please specify a correct time format like '30s', '2m', '1h', etc., and ensure it is less than 1 month.")
            return

        # Create a Reminder instance
        if recipient == "me":
            recipient = user
            reminder_message = reminder_message or "No message"
            reminder = Reminder(
                creator=user, recipient=recipient, time_ago=time_str, message=reminder_message)
            display_message = reminder.display_reminder()
        else:
            reminder = Reminder(
                creator=user, recipient=recipient, time_ago=time_str, message=reminder_message)
            display_message = reminder.display_reminder()

        # Schedule the reminder
        schedule_reminder(self, seconds, display_message,
                          channel)

        # Confirm the reminder setup in chat
        self.send_privmsg(channel,
                          f"@{user}, I will remind {recipient} in {time_str}.")
    else:
        self.send_privmsg(channel,
                          f"@{user}, please wait before sending another reminder.")


def parse_remind_command(args):
    """
    Extract recipient, time (optional), and message (optional) from the command arguments.

    Example arguments:
    - 'me in 30s'
    - '@alice in 2h Hello'
    - '@bob in 3 days'
    - '@bob in 2m 30s Hello'

    :param args: Command arguments as a single string
    :return: recipient (str), time (str), message (str)
    """
    if not args:
        return None, None, None

    parts = args.split(' ', 2)  # Split into recipient, "in", and the rest

    if len(parts) < 3 or parts[1] != 'in':
        # Handle the case where time or "in" keyword is missing
        return parts[0].strip(), None, ' '.join(parts[1:]).strip() if len(parts) > 1 else None

    recipient = parts[0].strip()
    time_message = parts[2].strip()

    if recipient.startswith('@'):
        recipient = recipient[1:]  # Remove '@' if it's a mention

    # Split time and message based on known time formats
    time_parts = []
    message = ""

    for part in time_message.split():
        if any(char.isdigit() for char in part) and part[-1] in ['s', 'm', 'h', 'd']:
            time_parts.append(part)
        else:
            message += f"{part} "

    time_str = ' '.join(time_parts)
    message = message.strip() or None

    return recipient, time_str, message


def parse_time_to_seconds(time_str):
    """
    Parses a time string (e.g., '3h', '5min') into seconds and checks for valid time range.

    :param time_str: A time string to parse
    :return: Number of seconds represented by the string or None if invalid
    """
    MAX_SECONDS = 30 * 24 * 3600  # Maximum time limit of 30 days in seconds

    try:
        # Check if the format is like '30s', '2m', '1h'
        if time_str and time_str[-1] in ['s', 'm', 'h', 'd']:
            quantity = int(time_str[:-1])
            unit = time_str[-1]

            if quantity < 0:
                return None  # Negative quantity is not allowed

            if unit == 's':
                seconds = quantity
            elif unit == 'm':
                seconds = quantity * 60
            elif unit == 'h':
                seconds = quantity * 3600
            elif unit == 'd':
                seconds = quantity * 86400
            else:
                return None  # Invalid unit

            if seconds > MAX_SECONDS:
                return None  # Exceeds the maximum allowed time

            return seconds

        # Check for longer formats like 'seconds', 'minutes', etc.
        parts = time_str.split()
        if len(parts) != 2:
            return None

        quantity = int(parts[0])
        unit = parts[1].lower()

        if quantity < 0:
            return None  # Negative quantity is not allowed

        if unit in ['second', 'seconds']:
            seconds = quantity
        elif unit in ['minute', 'minutes']:
            seconds = quantity * 60
        elif unit in ['hour', 'hours']:
            seconds = quantity * 3600
        elif unit in ['day', 'days']:
            seconds = quantity * 86400
        else:
            return None  # Invalid unit

        if seconds > MAX_SECONDS:
            return None  # Exceeds the maximum allowed time

        return seconds
    except (ValueError, IndexError):
        return None  # Catch invalid format and indexing errors


def schedule_reminder(bot_instance, delay, message, channel):
    """
    Schedules a reminder to be sent after a specified delay.

    :param bot_instance: The bot instance that should send the reminder
    :param delay: The delay in seconds before the reminder is sent
    :param message: The message to send
    :param channel: The channel to send the reminder to
    """
    threading.Timer(delay, bot_instance.send_privmsg,
                    args=(channel, message)).start()
