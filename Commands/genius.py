import re
import time

import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
import config


def get_request(url: str, web: bool = False):
    if config.PROXY:
        req = requests.get(config.PROXY, headers={"url": url})
    else:
        req = requests.get(url)
    if web:
        return req.text
    return req.json()


def search(query: str) -> dict:
    encoded_query = quote(query)
    return get_request(f"https://genius.com/api/search?q={encoded_query}").get("response")


def get_lyrics(song_url: str):
    html = BeautifulSoup(
        get_request(song_url, web=True).replace('<br/>', '\n'),
        "html.parser"
    )

    lyrics_containers = html.find_all("div", {"data-lyrics-container": "true"})
    for c in lyrics_containers:
        for container in c.find_all("div", {"data-exclude-from-selection": "true"}):
            container.decompose()
    lyrics = " ".join([container.get_text() for container in lyrics_containers])
    lyrics = re.sub(r'\s+\n', '\n', lyrics)
    lyrics = re.sub(r'\n\s+', '\n', lyrics)
    return lyrics.strip().replace("\n", " ")


def reply_with_genius(self, message, timeout=30):
    last_call = self.state.get("genius-lyrics")
    if last_call and last_call > time.time() - timeout:
        return

    if not message['command']['botCommandParams']:
        m = f"@{message['tags']['display-name']}, please provide a query for Genius search. Include song name and artist for best result."
        self.send_privmsg(message['command']['channel'], m)
        return

    query = (message['command']['botCommandParams'])
    try:
        request = search(query)
        hits = request["hits"]
        if not hits:
            m = "No results found. Try a different search."
            self.send_privmsg(message['command']['channel'], m)
            return

        first_hit = hits[0]["result"]
        song_url = first_hit["url"]
        lyrics = get_lyrics(song_url)
        if not lyrics:
            self.send_privmsg(message['command']['channel'], "Lyrics not found!")
            return

        title = first_hit["full_title"]
        lyrics = title + " " + lyrics
        lyric_msgs = [lyrics[i:i + 480] for i in range(0, len(lyrics), 480)]

        self.state["genius-lyrics"] = time.time()

        for msg in lyric_msgs:
            self.send_privmsg(message['command']['channel'], msg)
            time.sleep(0.6)

    except Exception as e:
        error_msg = f"Error: {str(e)[:490]}"
        self.send_privmsg(message['command']['channel'], error_msg)
        return
