import threading
from Classes.reminder_class import Reminder
from Utils.utils import check_cooldown, fetch_cmd_data


def reply_with_reminder(self, message):
    cmd = fetch_cmd_data(self, message)
    if not check_cooldown(cmd.state, cmd.nick, cmd.cooldown): 
        return

    # Get the user's reminder count from MongoDB
    user_data = self.users.find_one({'user': cmd.nick})
    if user_data:
        reminder_count = user_data.get('reminderCount', 0)
    else:
        # If user is not found, initialize their reminderCount
        reminder_count = 0
        self.users.insert_one(
            {'user': cmd.nick, 'reminderCount': 0})

    # Check if the user has hit the reminder limit
    if reminder_count >= 5:
        self.send_privmsg(
            cmd.channel, f"{cmd.username}, you already have 5 pending reminders. Enough spamming.")
        return

    # Parse command parameters
    recipient, time_str, reminder_message = parse_remind_command(cmd.params)

    # Validate time_str
    if time_str is None:
        self.send_privmsg(
            cmd.channel, f"{cmd.username}, please specify a valid time for the reminder, like 'in 30s' or 'in 2h'.")
        return

    seconds = parse_time_to_seconds(time_str)
    # Check for minimum 1 minute (60 seconds)
    if seconds is None or seconds < 60:
        self.send_privmsg(
            cmd.channel, f"{cmd.username}, you must set a reminder for at least 1 minute. The maximum time you can remind someone is 1 month.")
        return

    # Create a Reminder instance
    reminder_message = reminder_message or "No message"
    if recipient == "me":
        recipient = cmd.username
    reminder = Reminder(
        creator=cmd.username, recipient=recipient, time_ago=time_str, message=reminder_message)
    display_message = reminder.display_reminder()

    # Schedule the reminder
    schedule_reminder(self, seconds, display_message, cmd.channel, cmd.username)

    # Increment the user's reminder count in the database
    self.users.update_one({'user': cmd.nick}, {
        '$inc': {'reminderCount': 1}})

    # Confirm the reminder setup in chat
    self.send_privmsg(cmd.channel, f"{cmd.username}, I will remind {recipient} in {time_str}.")


def schedule_reminder(bot_instance, delay, message, channel, user):
    """
    Schedules a reminder to be sent after a specified delay.
    After sending the reminder, decrement the user's reminder count in MongoDB.
    """
    def send_reminder():
        # Send the reminder
        bot_instance.send_privmsg(channel, message)

        # Decrement the user's reminder count in the database
        bot_instance.users.update_one(
            {'user': user.lower()}, {'$inc': {'reminderCount': -1}})

    threading.Timer(delay, send_reminder).start()


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
    MIN_SECONDS = 60  # Minimum time limit of 1 minute in seconds
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

            if seconds > MAX_SECONDS or seconds < MIN_SECONDS:
                return None  # Exceeds the maximum allowed time or below the minimum

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

        if seconds > MAX_SECONDS or seconds < MIN_SECONDS:
            return None  # Exceeds the maximum allowed time or below the minimum

        return seconds
    except (ValueError, IndexError):
        return None  # Catch invalid format and indexing errors
