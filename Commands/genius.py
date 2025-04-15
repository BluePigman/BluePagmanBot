import time
import requests
from bs4 import BeautifulSoup
import html2text

def reply_with_genius(self, message):
    if ("genius-lyrics" not in self.state or time.time() - self.state["genius-lyrics"] > 30):
        if not message['command']['botCommandParams']:
            m = f"@{message['tags']['display-name']}, please provide a query for Genius search. Include song name and artist for best result."
            self.send_privmsg(message['command']['channel'], m)
            return

        query = (message['command']['botCommandParams'])
        try:
            dumb_domain = "https://dumb.ducks.party/"
            url = f"{dumb_domain}/search?q={query}"
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
                
                if lyrics:
                    self.state[message['source']['nick']] = time.time()
                    lyrics = f"{song_title_text} by {song_artist_text}\n" + lyrics

                    # Remove 'LyricsHeader' divs
                    for header in lyrics.select("div[class^='LyricsHeader']"):
                        header.decompose()
                    
                    text_maker = html2text.HTML2Text()
                    text_maker.ignore_links = True
                    text_maker.ignore_emphasis = True
                    lyrics = text_maker.handle(str(lyrics))
                    lyrics = lyrics.replace("\n", " ")
                    lyrics = [lyrics[i:i+495] for i in range(0, len(lyrics), 495)]\

                for m in lyrics:
                    self.send_privmsg(message['command']['channel'], m)
                    time.sleep(0.75)

        except Exception as e:
            error_msg = f"Error: {str(e)[:490]}"
            self.send_privmsg(message['command']['channel'], error_msg)
            return
        
        

