import re
import time

import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
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
    encoded_query = quote(query)
    return get_request(f"https://genius.com/api/search?q={encoded_query}").get("response")


def get_lyrics(song_url: str):
    html = BeautifulSoup(
        get_request(song_url, web=True).replace('<br/>', '\n'),
        "html.parser"
    )

    # Extract clean song title
    title_tag = html.find("h2", class_=re.compile(r"LyricsHeader__Title"))
    song_title = title_tag.get_text(strip=True) if title_tag else ""

    # Scrape the lyrics from appropriate <div> blocks
    divs = html.find_all("div", class_=re.compile(r"^Lyrics-\w{2}.\w+.[1]|Lyrics__Container"))

    if not divs:
        return None

    lyrics = "\n".join([div.get_text(separator="\n").strip() for div in divs])

    # Clean up extra html text"
    if song_title and lyrics.startswith(song_title) is False:
        # Look for and trim everything before the real title
        lyrics_parts = lyrics.split(song_title, 1)
        if len(lyrics_parts) == 2:
            lyrics = f"{song_title}\n{lyrics_parts[1].strip()}"
    elif song_title:
        lyrics = f"{song_title}\n{lyrics}"

    return lyrics.strip()


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

        if not lyrics:
            self.send_privmsg(message['command']['channel'], "Lyrics not found!")
            return

        lyrics = lyrics.replace("\n", " ")
        lyrics = [lyrics[i:i + 480] for i in range(0, len(lyrics), 480)]
        for m in lyrics:
            self.send_privmsg(message['command']['channel'], m)
            time.sleep(0.6)

    except Exception as e:
        error_msg = f"Error: {str(e)[:490]}"
        self.send_privmsg(message['command']['channel'], error_msg)
        return
