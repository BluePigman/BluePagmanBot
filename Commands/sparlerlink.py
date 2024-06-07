import random
import time
import requests
from urllib.parse import quote

def reply_with_sparlerlink(self, message):
    if (message.user not in self.state or time.time() - self.state[message.user] > self.cooldown):
        self.state[message.user] = time.time()

        
        url = "https://pr0gramm.com/api/items/get?flags=1"
        
        

        if (message.text_args):
            
            input_text = ' '.join(message.text_args)

            if "-p" in input_text:
                input_text = input_text[:input_text.index("-p")]
                url += "&promoted=1"
                
            keywords = ' '.join(message.text_args)
            if '\U000e0000' in keywords:
                keywords = keywords.replace('\U000e0000', '')
            keywords = keywords.replace(" ", "+")
            keywords = keywords.replace("#", "'#'")
            keywords = keywords.replace("&", "'&'")
            url += f"&tags={keywords}"

        try:
            print(url)
            response = requests.get(url)
            response.raise_for_status()
            data = response.json().get('items', [])
            
            if len(data) < 1:
                self.send_privmsg(message.channel, "No link for @Sparler :(")
            else:
                random_item = data[random.randint(0, len(data) - 1)]
                text = f"https://vid.pr0gramm.com/{random_item['image']}"
                self.send_privmsg(message.channel, text)
        except Exception as e:
            self.send_privmsg(message.channel, "No link for @Sparler :( (something went wrong)")
