from datetime import datetime, timedelta, timezone
from Utils.utils import check_cooldown, fetch_cmd_data, proxy_request

LOGS_API = "https://logs.zonian.dev/channel"

# time span
SPAN = timedelta(minutes=5)

# message threshold
BASELINE = 6


def _fetch_messages(channel, date):
    try:
        url = (
            f"{LOGS_API}/"
            f"{channel}/"
            f"{date.year}/"
            f"{date.month}/"
            f"{date.day}"
        )

        r = proxy_request(
            "GET",
            url,
            params={"jsonBasic": 1}
        )

        if not r.ok:
            return None

        try:
            data = r.json()
        except Exception:
            return None

        msgs = data.get("messages")
        return msgs if isinstance(msgs, list) else None

    except Exception:
        return None


def _parse_timestamp(ts):
    try:
        if not ts:
            return None
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except Exception:
        return None


def _count_messages(messages, start, end, exclude_text):
    count = 0

    for msg in messages:
        if not isinstance(msg, dict):
            continue

        text = msg.get("text", "")
        if not isinstance(text, str):
            continue

        if exclude_text in text:
            continue

        t = _parse_timestamp(msg.get("timestamp"))
        if t and start <= t < end:
            count += 1

    return count


def _get_window():
    now = datetime.now(timezone.utc)
    return now - SPAN, now


def _classify(count):
    return "alive" if count >= BASELINE else "dead"


def _get_activity(channel, exclude_text):
    try:
        start, end = _get_window()

        msgs = _fetch_messages(channel, end)

        if msgs is None:
            return None

        if start.date() != end.date():
            prev_msgs = _fetch_messages(channel, start)
            if prev_msgs is None:
                return None
            msgs = prev_msgs + msgs

        count = _count_messages(msgs, start, end, exclude_text)

        return {
            "count": int(count),
            "minutes": int(SPAN.total_seconds() / 60),
            "state": _classify(count)
        }

    except Exception:
        return None


def reply_with_message_rate(self, message):
    try:
        cmd = fetch_cmd_data(self, message)

        if not check_cooldown(cmd.state, cmd.nick, cmd.cooldown):
            return

        data = _get_activity(cmd.channel, self.prefix)

        if data is None:
            self.send_privmsg(cmd.channel, "Failed to fetch message data!")
            return

        count = data["count"]
        minutes = data["minutes"]
        state = data["state"]

        prefix = f"Messages in the past {minutes} minutes: {count}"

        if state == "alive":
            msg = f"{prefix} Alive chat Pog"
        else:
            msg = f"{prefix} deadchatxd"

        self.send_privmsg(cmd.channel, msg)

    except Exception:
        self.send_privmsg(cmd.channel, "An unexpected error occurred while fetching message data.")
