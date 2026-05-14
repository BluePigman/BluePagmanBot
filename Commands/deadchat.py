from datetime import datetime, timedelta, timezone
from Utils.utils import check_cooldown, fetch_cmd_data, proxy_request

LOGS_API = "https://logs.zonian.dev/channel"

# default time span
DEFAULT_SPAN_MINUTES = 5

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
            params={
                "jsonBasic": 1,
                "rm_only": "true" # makes it faster according to the docs https://logs.zonian.dev/api
            }
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

        if text.startswith(exclude_text):
            continue

        t = _parse_timestamp(msg.get("timestamp"))
        if t and start <= t < end:
            count += 1

    return count


def _get_window(span):
    now = datetime.now(timezone.utc)
    return {"start": now - span, "end": now}


def _classify(count):
    return "alive" if count >= BASELINE else "dead"


def _get_activity(channel, exclude_text, span):
    try:
        window = _get_window(span)
        start = window["start"]
        end = window["end"]

        msgs = _fetch_messages(channel, end)

        if msgs is None:
            return None

        # handle messages at midnight
        if start.date() != end.date():
            prev_day_msgs = _fetch_messages(channel, start)
            if prev_day_msgs is None:
                return None
            msgs = prev_day_msgs + msgs

        count = _count_messages(msgs, start, end, exclude_text)

        return {
            "count": int(count),
            "minutes": int(span.total_seconds() / 60),
            "state": _classify(count)
        }

    except Exception:
        return None


def reply_with_message_rate(self, message):
    try:
        cmd = fetch_cmd_data(self, message, arg_types={ "m": int })

        if not check_cooldown(cmd.state, cmd.nick, cmd.cooldown):
            return

        minutes = cmd.args.get("m", DEFAULT_SPAN_MINUTES)

        if not (0 < minutes <= 1440): # 1 day (1440 minutes)
            self.send_privmsg(cmd.channel, "Minutes must be between 1 and 1440 (1 day).")
            return

        span = timedelta(minutes=minutes)

        data = _get_activity(cmd.channel, self.prefix, span)

        if data is None:
            self.send_privmsg(cmd.channel, "Failed to fetch message data!")
            return

        count = data["count"]
        minutes = data["minutes"]
        state = data["state"]

        prefix = f"Messages in the past {minutes} minutes: {count}"

        if state == "alive":
            msg = f"{prefix} alive chat Pog"
        else:
            msg = f"{prefix} deadchatxd"

        self.send_privmsg(cmd.channel, msg)

    except Exception:
        self.send_privmsg(cmd.channel, "An unexpected error occurred while fetching message data.")
