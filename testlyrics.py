from lyricsgenius import Genius
import config
import re
genius = Genius(config.GENIUS_TOKEN)

request = genius.search("motion sickness")
if not request["hits"]:
    m = "No results found. Try a different search."
    print(m)
else:    

    songId = request["hits"][0]["result"]["id"]
    lyrics = genius.lyrics(song_id=songId)
    lyrics = lyrics.replace("\\n", " ")
    lyrics = str(re.sub(r'\n+', ' ', lyrics).strip())
    lyrics = [lyrics[i:i+495] for i in range(0, len(lyrics), 495)]
    print(lyrics)