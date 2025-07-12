import xml.etree.ElementTree as ET

import requests
from bs4 import BeautifulSoup

from Utils.utils import fetch_cmd_data, check_cooldown, CHUNK_SIZE, format_time_ago


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

    response = requests.get("https://trumpstruth.org/feed", timeout=5)
    if response.status_code != 200:
        self.send_privmsg(message['command']['channel'],
                          "Failed to fetch the latest post from https://trumpstruth.org/feed. status code " + str(
                              response.status_code))
        return

    root = ET.fromstring(response.content)
    channel = root.find('channel')
    if channel is None:
        self.send_privmsg(message['command']['channel'], "No channel found in RSS feed. https://trumpstruth.org/feed")
        return
    items = channel.findall('item')
    if not items:
        self.send_privmsg(message['command']['channel'], "No items found in RSS feed. https://trumpstruth.org/feed")
        return

    latest_item = items[0]
    description = latest_item.find('description').text if latest_item.find(
        'description') is not None else ''

    soup = BeautifulSoup(description, "html.parser")
    clean_text = soup.get_text().strip()
    time_part = format_time_ago(latest_item.find('pubDate').text)
    max_content_len = CHUNK_SIZE - len("TRUTH ") - 1

    truncated_text = truncate_with_suffix(clean_text, time_part, max_length=max_content_len)
    msg = "TRUTH " + truncated_text
    self.send_privmsg(cmd.channel, msg)
