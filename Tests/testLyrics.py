from Commands import genius
import time

def run_test(query, description=""):
    print(f"\n--- Testing {description} (Query: '{query}') ---")
    request = genius.search(query)

    if not request["hits"]:
        print("No hits found.")
    else:
        song_url = request["hits"][0]["result"]["url"]
        print(f"URL: {song_url}")
        lyrics = genius.get_lyrics(song_url)

        if lyrics is None:
            print("Couldn't extract lyrics. The Genius HTML structure may have changed.")
        else:
            lyrics_short = lyrics[:100]
            msg = f"Lyrics found (first 100 chars): {lyrics_short}"
            if len(lyrics) > 100:
                msg +=  f"...  \nTotal length: {len(lyrics)}"
            print(msg)
    time.sleep(1)

# Test Case 1: Regular Lyrics
run_test("motion sickness", "Regular Lyrics")

# Test Case 2: Instrumental
run_test("aria math c418", "Instrumental")

# Test Case 3: Unreleased
run_test("To be announced midwxst", "Unreleased")