import json
import time
from datetime import datetime, timezone
from typing import Any, Optional

import curl_cffi
from bs4 import BeautifulSoup
from curl_cffi import requests
from dateutil import parser as date_parse

import config


class TruthSocialApi:
    BASE_URL = "https://truthsocial.com"
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
        self.ratelimit_max = 300
        self.ratelimit_remaining = None
        self.ratelimit_reset = None
        self.token = token

    def _get(self, url: str, params: dict = None) -> Any:
        try:
            resp = requests.Session().get(
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


def truthsocial(self, message):
    if not (message['source']['nick'] not in self.state or time.time() - self.state[message['source']['nick']] >
            self.cooldown):
        return
    self.state[message['source']['nick']] = time.time()

    resp = api.pull_latest_status(user_id=TRUMP_USER_ID)
    if not resp or len(resp) == 0:
        self.send_privmsg(message['command']['channel'], "No recent posts found.")
        return

    latest = resp[0]
    content_html = latest.get("content", "")
    created_at_str = latest.get("created_at")
    attachments = latest.get("media_attachments", [])

    soup = BeautifulSoup(content_html, "html.parser")
    clean_text = soup.get_text().strip()

    try:
        created_at = date_parse.parse(created_at_str)
        now = datetime.now(timezone.utc)
        delta = now - created_at
        days = delta.days
        hours = delta.seconds // 3600
        minutes = (delta.seconds % 3600) // 60
        if days > 0:
            time_part = f"(posted {days}d {hours}h {minutes}m ago)"
        else:
            time_part = f"(posted {hours}h {minutes}m ago)"
    except Exception:
        time_part = ""
    # Handle video-only posts
    if not clean_text and attachments:
        video = next((m.get("url") for m in attachments if m.get("type") == "video"), None)
        if video:
            msg = f"Video post: {video} {time_part}".strip()
            self.send_privmsg(message['command']['channel'], msg[:500])
            return

    msg = f"TRUTH {clean_text} {time_part}".strip()
    if len(msg) > 500:
        msg = msg[:495] + "..."
    self.send_privmsg(message['command']['channel'], msg)
