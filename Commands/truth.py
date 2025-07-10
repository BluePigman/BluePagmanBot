import json
from typing import Optional

from bs4 import BeautifulSoup

import config
from Utils.utils import fetch_cmd_data, check_cooldown, CHUNK_SIZE, format_time_ago, impersonated_request


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

    def _get(self, url: str, params: dict = None) -> Optional[dict]:
        resp = impersonated_request("GET", self.API_BASE_URL + url, params=params, headers={
            "Authorization": "Bearer " + self.token,
            "User-Agent": self.USER_AGENT,
        })

        if resp.status_code == 429:
            raise RateLimitExceeded("Truth Social API Rate limit exceeded. Please try again later.")

        if resp.status_code != 200:
            raise UnknownError(f"Truth Social API returned an unexpected status code: {resp.status_code}")

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


def truncate_with_suffix(text: str, suffix: str, max_length: int = CHUNK_SIZE) -> str:
    ellipsis = "..."
    space = " " if suffix else ""
    total_suffix = ellipsis + space + suffix  # e.g. "... (posted 10m ago)"

    if len(text) + len(space + suffix) <= max_length:
        return text + space + suffix

    # Reserve space for the suffix and ellipsis
    max_text_len = max_length - len(total_suffix)

    if max_text_len <= 0:
        # Not enough room for even a single char + suffix
        return suffix[:max_length]

    return text[:max_text_len].rstrip() + total_suffix


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
    max_content_len = CHUNK_SIZE - len("TRUTH ") - 1

    if not clean_text and attachments:
        video = next((m.get("url") for m in attachments if m.get("type") == "video"), None)
        if video:
            truncated_video = truncate_with_suffix(video, time_part, max_length=max_content_len)
            msg = "TRUTH " + truncated_video
            self.send_privmsg(cmd.channel, msg)
            return

    truncated_text = truncate_with_suffix(clean_text, time_part, max_length=max_content_len)
    msg = "TRUTH " + truncated_text
    self.send_privmsg(cmd.channel, msg)
