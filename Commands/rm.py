import json
import random
import time
import requests
from bs4 import BeautifulSoup
def reply_with_rm(self, message):
    if (message['source']['nick'] not in self.state or time.time() - self.state[message['source']['nick']] > self.cooldown):
        self.state[message['source']['nick']] = time.time()
        
        if not message['command']['botCommandParams']:
            subreddit = "all"
        else:
            subreddit = message['command']['botCommandParams'].split()[0]
        
        post_dict = scrape_subreddit(subreddit)
        if not post_dict:
            self.send_privmsg(message['command']['channel'], "No posts found.")
            return
        subName = post_dict['subreddit']
        title = post_dict['title']
        url =  post_dict['link']
        score = post_dict['score']
        time_posted = post_dict['time_posted']
        msg = f"{subName}: {title} {url} (Score: {score}, posted {time_posted})"

        self.send_privmsg(message['command']['channel'], msg)



def scrape_subreddit(subreddit):
    url = f"https://l.opnxng.com/r/{subreddit}"
    response = requests.get(url)
    html_content = response.content

    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(html_content, features="html.parser",from_encoding='utf-8')

    # Find all posts
    posts = soup.find_all("div", class_="post")

    post_data = []
    for post in posts:
        if "post stickied" == " ".join(post.get("class", [])):
            continue
        title_links = post.find("h2", class_="post_title").find_all("a")
        if len(title_links) == 1:
            title = title_links[0].get_text(strip=True)
        elif len(title_links) > 1:
            title = title_links[1].get_text(strip=True)
        else:
            title = None
        title = title.replace("\u2019", "'") if title else None
        title = title.replace('\u201c', '"') if title else None
        title = title.replace('\u201d', '"') if title else None

        media_link = post.find("div", class_="post_media_content")
        thumbnail_link = post.find("a", class_="post_thumbnail")
        
        if media_link:
            link = media_link.find("a")["href"]
            link = f"https://l.opnxng.com{link}"
        elif thumbnail_link:
            link = thumbnail_link["href"]
            link = link
        elif len(title_links) > 0:
            link = title_links[0]["href"]
            link = link
        else:
            link = None

        if link and link.startswith("/r/"):
            link = f"https://l.opnxng.com{link}"
        
        if link.startswith("/gallery"):
            link = f"https://reddit.com{link}"

        # Extract the time posted and score
        time_posted = post.find("span", class_="created")["title"] if post.find("span", class_="created") else None
        score = post.find("div", class_="post_score").get_text(strip=True).replace(' Upvotes', '') if post.find("div", class_="post_score") else None
        score = score.replace('Upvotes', '') if score else None
        score = score.replace("\u2022", "Idk ") if score else None
        
        subreddit = post.find("a", class_="post_subreddit").get_text(strip=True)
        # Create a dictionary for the post
        post_dict = {
            "title": title,
            "link": link,
            "time_posted": time_posted,
            "score": score,
            "subreddit": subreddit
        }
        post_data.append(post_dict)
    if not post_data:
        return None
    return(random.choice(post_data))

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