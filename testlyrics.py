import requests
from bs4 import BeautifulSoup
import html2text

query = "motion sickness"
dumb_domain = "https://dumb.ducks.party/"
url = f"{dumb_domain}/search?q={query}"

try:
    response = requests.get(url)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'html.parser')

    first_song_link = None
    song_artist_text = ""
    song_title_text = ""

    for a in soup.find_all('a', id="search-item", href=True):
        if a['href'].endswith('lyrics'):
            first_song_link = a['href']
            song_artist = a.find('span')
            song_title = a.find('h3')
            
            if song_artist:
                song_artist_text = song_artist.get_text(strip=True)
            if song_title:
                song_title_text = song_title.get_text(strip=True)
            
            break

    if first_song_link:
        song_url = dumb_domain + first_song_link.lstrip('/')
        dumb_response = requests.get(song_url)
        dumb_response.encoding = 'utf-8'
        soup = BeautifulSoup(dumb_response.text, 'html.parser')
        lyrics = soup.select_one("#lyrics")
        
        print(f"{song_title_text} by {song_artist_text}\n")
        
        if lyrics:
            # Remove 'LyricsHeader' divs
            for header in lyrics.select("div[class^='LyricsHeader']"):
                header.decompose()
            
            text_maker = html2text.HTML2Text()
            text_maker.ignore_links = True
            text_maker.ignore_emphasis = True
            lyrics = text_maker.handle(str(lyrics))
            lyrics = lyrics.replace("\n", " ")
            lyrics = [lyrics[i:i+495] for i in range(0, len(lyrics), 495)]
            print(lyrics)
        else:
            print("Lyrics not found")
    else:
        print("No lyrics link found")

except Exception as e:
    print(e)