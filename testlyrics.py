from lyricsgenius import Genius
import config
import re
userAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
genius = Genius(access_token=config.GENIUS_TOKEN, user_agent=userAgent)

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