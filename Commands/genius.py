import re
import time

import requests
from bs4 import BeautifulSoup

import config


def get_request(url: str, web: bool = False):
    if config.GENIUS_PROXY:
        req = requests.get(config.GENIUS_PROXY, headers={"url": url})
    else:
        req = requests.get(url)
    if web:
        return req.text
    return req.json()


def search(query: str) -> dict:
    return get_request(f"https://genius.com/api/search?q={query}").get("response")


def get_lyrics(song_url=None, remove_section_headers=False):
    # Scrape the song lyrics from the HTML
    html = BeautifulSoup(
        get_request(song_url, web=True).replace('<br/>', '\n'),
        "html.parser"
    )

    # Determine the class of the div
    divs = html.find_all("div", class_=re.compile(r"^Lyrics-\w{2}.\w+.[1]|Lyrics__Container"))
    if divs is None or len(divs) <= 0:
        return None

    lyrics = "\n".join([div.get_text() for div in divs])

    # Remove [Verse], [Bridge], etc.
    if remove_section_headers:
        lyrics = re.sub(r'(\[.*?\])*', '', lyrics)
        lyrics = re.sub('\n{2}', '\n', lyrics)  # Gaps between verses
    return lyrics.strip("\n")


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
        if not request["hits"]:
            m = "No results found. Try a different search."
            self.send_privmsg(message['command']['channel'], m)
            return
        self.state["genius-lyrics"] = time.time()
        song_url = request["hits"][0]["result"]["url"]
        lyrics = get_lyrics(song_url)
        lyrics = lyrics.replace("\\n", " ")
        lyrics = str(re.sub(r'\n+', ' ', lyrics).strip())
        lyrics = [lyrics[i:i + 480] for i in range(0, len(lyrics), 480)]
        for m in lyrics:
            self.send_privmsg(message['command']['channel'], m)
            time.sleep(0.6)

    except Exception as e:
        error_msg = f"Error: {str(e)[:490]}"
        self.send_privmsg(message['command']['channel'], error_msg)
        return
