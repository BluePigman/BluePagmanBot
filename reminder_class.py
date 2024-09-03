from datetime import datetime, timedelta


class Reminder:
    def __init__(self, creator: str, recipient: str, time_ago: str, message: str = None, ):
        """
        Initializes a Reminder object.

        :param creator: Name of the user who created the reminder.
        :param recipient: Name of the user who the reminder is intended for.
        :param message: The reminder message. Defaults to None.
        :param time_ago: How long ago the reminder was created. 
        """
        self.creator = creator
        self.recipient = recipient
        self.time_created = datetime.now()
        self.time_ago = time_ago
        self.message = message

    def display_reminder(self):
        """
        Returns the formatted reminder message for displaying in chat.

        :return: A string formatted as a chat message.
        """
        # Calculate the time since the reminder was created
        time_elapsed = datetime.now() - self.time_created
        time_elapsed_str = self.format_time_delta(time_elapsed)

        # Format the message for chat display
        if self.creator == self.recipient:
            return f"@{self.recipient}, reminder from yourself, ({self.time_ago} ago): {self.message or '(No message)'}"
        else:
            return f"@{self.recipient}, timed reminder from @{self.creator}, ({self.time_ago} ago): {self.message or '(No message)'}"

    @staticmethod
    def format_time_delta(delta: timedelta) -> str:
        """
        Formats a timedelta object into a string with hours, minutes, and seconds.

        :param delta: A timedelta object representing the duration.
        :return: A string formatted as 'xh ym zs'.
        """
        seconds = int(delta.total_seconds())
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60

        parts = []
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
        if seconds > 0 or not parts:  # Include seconds if no other parts are present
            parts.append(f"{seconds}s")

        return ' '.join(parts)
