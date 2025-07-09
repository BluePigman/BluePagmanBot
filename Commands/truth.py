import json
import time
from datetime import datetime, timezone
from typing import Optional

import curl_cffi
from bs4 import BeautifulSoup
from curl_cffi import requests
from dateutil import parser as date_parse

import config
from Utils.utils import fetch_cmd_data, send_chunks, check_cooldown


class RateLimitExceeded(Exception):
    pass


class UnknownError(Exception):
    pass


class TruthSocialApi:
    API_BASE_URL = "https://truthsocial.com/api"
    USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 "
        "Safari/537.36"
    )

    CLIENT_ID = "9X1Fdd-pxNsAgEDNi_SfhJWi8T-vLuV2WVzKIbkTCw4"
    CLIENT_SECRET = "ozF8jzI4968oTKFkEnsBC-UbLPCdrSv0MkXGQu2o_-M"

    def __init__(
            self,
            token: str,
    ):
        self.token = token
        self.session = requests.Session()

    def _get(self, url: str, params: dict = None) -> Optional[dict]:
        try:
            resp = self.session.get(
                self.API_BASE_URL + url,
                params=params,
                impersonate="chrome123",
                headers={
                    "Authorization": "Bearer " + self.token,
                    "User-Agent": self.USER_AGENT,
                },
            )
        except curl_cffi.curl.CurlError as e:
            print(f"Curl error: {e}")
            return None

        if resp.status_code == 429:
            raise RateLimitExceeded("Truth Social API Rate limit exceeded. Try again later.")

        if resp.status_code != 200:
            raise UnknownError(f"Truth Social API Unexpected status code: {resp.status_code}")

        try:
            r = resp.json()
        except json.JSONDecodeError:
            print(f"Failed to decode JSON: {resp.text}")
            r = None
        return r

    def lookup(self, user_handle: str) -> Optional[dict]:
        """Lookup a user's information."""
        return self._get("/v1/accounts/lookup", params=dict(acct=user_handle))

    def pull_latest_status(self, user_id: str):
        return self._get(f"/v1/accounts/{user_id}/statuses?exclude_replies=true&only_replies=false&with_muted=true")


api = TruthSocialApi(token=config.TRUTHSOCIAL_KEY)
TRUMP_USER_ID = "107780257626128497"


def format_time_ago(created_at_str: str) -> str:
    """Format a datetime string into a human-readable 'time ago' format."""
    if not created_at_str:
        return ""

    try:
        created_at = date_parse.parse(created_at_str)
        now = datetime.now(timezone.utc)

        # Ensure both datetimes are timezone-aware
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)

        delta = now - created_at
        # Handle negative deltas (future dates)
        if delta.total_seconds() < 0:
            return "(posted in the future?)"

        days = delta.days
        hours = delta.seconds // 3600
        minutes = (delta.seconds % 3600) // 60

        if days > 0:
            return f"(posted {days}d {hours}h {minutes}m ago)"
        elif hours > 0:
            return f"(posted {hours}h {minutes}m ago)"
        elif minutes > 0:
            return f"(posted {minutes}m ago)"
        else:
            return "(posted just now)"

    except (ValueError, TypeError, OverflowError) as e:
        print(f"Date parsing error: {e} for date string: {created_at_str}")
        return "(posted at unknown time)"
    except Exception as e:
        print(f"Unexpected error in date formatting: {e}")
        return ""


def truthsocial(self, message):
    cmd = fetch_cmd_data(self, message)
    if not check_cooldown(cmd.state, cmd.nick, cmd.cooldown):
        return

    try:
        resp = api.pull_latest_status(user_id=TRUMP_USER_ID)
    except RateLimitExceeded as e:
        self.send_privmsg(message['command']['channel'], str(e))
        return
    except UnknownError as e:
        self.send_privmsg(message['command']['channel'], str(e))
        return

    if not resp or len(resp) == 0:
        self.send_privmsg(message['command']['channel'], "No recent posts found.")
        return

    latest = resp[0]
    content_html = latest.get("content", "")
    created_at_str = latest.get("created_at")
    attachments = latest.get("media_attachments", [])

    soup = BeautifulSoup(content_html, "html.parser")
    clean_text = soup.get_text().strip()
    time_part = format_time_ago(created_at_str)
    if not clean_text and attachments:
        video = next((m.get("url") for m in attachments if m.get("type") == "video"), None)
        if video:
            msg = f"TRUTH {video} {time_part}".strip()
            send_chunks(self.send_privmsg, cmd.channel, msg, delay=0.6)
            return

    msg = f"TRUTH {clean_text} {time_part}".strip()
    send_chunks(self.send_privmsg, cmd.channel, msg, delay=0.6)
