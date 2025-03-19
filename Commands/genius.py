import time
from lyricsgenius import Genius
import config
import re
genius = Genius(config.GENIUS_TOKEN)


def reply_with_genius(self, message):
    if ("genius-lyrics" not in self.state or time.time() - self.state["genius-lyrics"] > 30):
        if not message['command']['botCommandParams']:
            m = f"@{message['tags']['display-name']}, please provide a query for Genius search. Include song name and artist for best result."
            self.send_privmsg(message['command']['channel'], m)
            return

        query = (message['command']['botCommandParams'])
        request = genius.search(query)
        if not request["hits"]:
            m = "No results found. Try a different search."
            self.send_privmsg(message['command']['channel'], m)
            return
        
        self.state["genius-lyrics"] = time.time()
        songId = request["hits"][0]["result"]["id"]
        lyrics = genius.lyrics(song_id=songId)
        lyrics = lyrics.replace("\\n", " ")
        lyrics = str(re.sub(r'\n+', ' ', lyrics).strip())
        lyrics = [lyrics[i:i+495] for i in range(0, len(lyrics), 495)]
        for m in lyrics:
            self.send_privmsg(message['command']['channel'], m)
            time.sleep(0.4)

