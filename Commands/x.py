import time

def convert_twitter_link(link:str):
    return link.replace("x.com", "xcancel.com")


def reply_with_x(self, message):
    if "twitter.com/" in message['command']['botCommandParams'] or "x.com" in message['command']['botCommandParams']:
         # Extract and convert Twitter link
        message['command']['botCommandParams'] = message['command']['botCommandParams'].replace("twitter.com", "x.com")
        words = message['command']['botCommandParams'].split()
        twitter_link = next((word for word in words if "x.com/" in word), None)
        
        if twitter_link:
            xcancel_link = twitter_link.replace("x.com", "xcancel.com")
            self.send_privmsg(message['command']['channel'], xcancel_link)