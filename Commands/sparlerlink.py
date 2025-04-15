import random
import time
import requests

def reply_with_sparlerlink(self, message):
    if (message['source']['nick'] not in self.state or time.time() - self.state[message['source']['nick']] > self.cooldown):
        self.state[message['source']['nick']] = time.time()

        url = "https://pr0gramm.com/api/items/get?flags=1"
        
        if (message['command']['botCommandParams']):
            input_text = message['command']['botCommandParams']

            if "-p" in input_text:
                input_text = input_text[:input_text.index("-p")]
                url += "&promoted=1"
                
            keywords = input_text
            if '\U000e0000' in keywords:
                keywords = keywords.replace('\U000e0000', '')
            keywords = keywords.replace(" ", "+")
            keywords = keywords.replace("#", "'#'")
            keywords = keywords.replace("&", "'&'")
            url += f"&tags={keywords}"

        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json().get('items', [])
            
            if len(data) < 1:
                self.send_privmsg(message['command']['channel'], "No link for @Sparler :(")
            else:
                random_item = data[random.randint(0, len(data) - 1)]
                text = f"https://vid.pr0gramm.com/{random_item['image']}"
                self.send_privmsg(message['command']['channel'], text)

        except Exception as e:
            self.send_privmsg(message['command']['channel'], "No link for @Sparler :( (something went wrong)")
