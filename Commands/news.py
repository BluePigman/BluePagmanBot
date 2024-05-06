import time
import newsCommands
def reply_with_news(self, message):
    if (message.user not in self.state or time.time() - self.state[message.user] > self.cooldown):
        self.state[message.user] = time.time()
        try:
            m = newsCommands.get_random_news_item()
            if (message.text_args):
                keywords = ' '.join(message.text_args)
                if '\U000e0000' in keywords:
                    keywords = keywords.replace('\U000e0000', '')
                keywords = keywords.replace(" ", "+")
                keywords = keywords.replace("#", "'#'")
                keywords = keywords.replace("&", "'&'")
                m = newsCommands.get_random_news_item(keywords)
            self.send_privmsg(message.channel, m)
        except Exception as e:
            print(e)
            self.send_privmsg(message.channel, f"@{message.user}, No news found for the given query.")