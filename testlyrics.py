from Commands import genius
import re

query = "motion sickness"
request = genius.search(query)

if not request["hits"]:
    print("No results found. Try a different search.")
else:
    song_url = request["hits"][0]["result"]["url"]
    lyrics = genius.get_lyrics(song_url)

    if lyrics is None:
        print("Couldn't extract lyrics. The Genius HTML structure may have changed.")
    else:
        lyrics = re.sub(r'\s+', ' ', lyrics).strip()

        chunks = [lyrics[i:i+495] for i in range(0, len(lyrics), 495)]

        for i, chunk in enumerate(chunks, 1):
            print(f"--- Chunk {i} ---\n{chunk}\n")