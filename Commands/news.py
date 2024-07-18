import time
import newsCommands
def reply_with_news(self, message):
    if (message['source']['nick'] not in self.state or time.time() - self.state[message['source']['nick']] > self.cooldown):
        self.state[message['source']['nick']] = time.time()
        try:
            if (message['command']['botCommandParams']):
                keywords = ' '.join(message['command']['botCommandParams'])
                if '\U000e0000' in keywords:
                    keywords = keywords.replace('\U000e0000', '')
                keywords = keywords.replace(" ", "+")
                keywords = keywords.replace("#", "'#'")
                keywords = keywords.replace("&", "'&'")
                m = newsCommands.get_random_news_item(keywords)
            else:
                m = newsCommands.get_random_news_item()
            print(m)
            self.send_privmsg(message['command']['channel'], m) 
        except Exception as e:
            print(e)
            self.send_privmsg(message['command']['channel'], f"Error: {str(e)[:300]}")