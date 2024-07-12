import random
import time
import requests
def reply_with_rm(self, message):
    if (message['source']['nick'] not in self.state or time.time() - self.state[message['source']['nick']] > self.cooldown):
        self.state[message['source']['nick']] = time.time()
        
        if not message['command']['botCommandParams']:
            subreddit = "all"
        else:
            subreddit = message['command']['botCommandParams'].split()[0]
        url = f"https://reddit.com/r/{subreddit}/hot.json"

        response = requests.get(url)
        if response.status_code == 403:
            self.send_privmsg(message['command']['channel'], "Reddit is rate limited! Wait 10 minutes for more.")
            return
        data = response.json()
        posts = data["data"]["children"]
        if len(posts) == 0:
            self.send_privmsg(message['command']['channel'], "Subreddit not found!")
            return
        posts = [post for post in posts if not post['data']['stickied']]
        
        post = random.choice(posts)
        url =  post["data"]["url"]
        subName = post["data"]["subreddit_name_prefixed"]
        title = post["data"]["title"]
        score = post["data"]["score"]
        created_utc = post["data"]["created_utc"]
        createdAgo = format_time_ago(created_utc)
        msg = f"{subName}: {title} {url} (Score: {score}, posted {createdAgo})"

        self.send_privmsg(message['command']['channel'], msg)


def format_time_ago(created_utc):
    now = time.time()
    diff = now - created_utc

    days, remainder = divmod(diff, 86400)
    hours, remainder = divmod(remainder, 3600) 
    minutes, _ = divmod(remainder, 60)  

    days = int(days)
    hours = int(hours)
    minutes = int(minutes)

    if days >= 365:
        years = days // 365
        remaining_days = days % 365
        return f"{years}y, {remaining_days}d ago"
    elif days > 0:
        return f"{days}d, {hours}h ago"
    elif hours > 0:
        return f"{hours}h, {minutes}m ago"
    else:
        return f"{minutes}m ago"