from datetime import datetime
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
    url = f"https://redlib.catsarch.com/r/{subreddit}"
    response = requests.get(url)
    html_content = response.content

    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(html_content, features="html.parser", from_encoding='utf-8')

    # Find all posts
    posts = soup.find_all("div", class_="post")

    post_data = []
    for post in posts:
        # Skip stickied posts
        if "stickied" in post.get("class", []):
            continue

        # Get title and link
        title_element = post.find("h2", class_="post_title")
        if title_element:
            # Get all links and take the last one (skipping flairs)
            title_links = title_element.find_all("a")
            if title_links:
                # Skip flair links by checking for post_flair class
                post_link = None
                for link in title_links:
                    if 'post_flair' not in link.get('class', []):
                        post_link = link
                
                if post_link:
                    title = post_link.get_text(strip=True)
                    link = post_link["href"]
                    # Add domain if it's a relative URL
                    if link.startswith("/"):
                        link = f"https://redlib.catsarch.com{link}"
                    
                    # Clean up title
                    title = title.replace("\u2019", "'")
                    title = title.replace('\u201c', '"')
                    title = title.replace('\u201d', '"')

                    # Get time posted and format it
                    time_element = post.find("span", class_="created")
                    if time_element and "title" in time_element.attrs:
                        timestamp_str = time_element["title"]
                        try:
                            # Parse the timestamp string to datetime object
                            dt = datetime.strptime(timestamp_str, "%b %d %Y, %H:%M:%S UTC")
                            # Convert to Unix timestamp
                            created_utc = dt.timestamp()
                            time_posted = format_time_ago(created_utc)
                        except ValueError:
                            time_posted = time_element.get_text(strip=True)
                    else:
                        time_posted = None

                    # Get score
                    score_element = post.find("div", class_="post_score")
                    if score_element:
                        score = score_element.get_text(strip=True)
                        score = score.replace("Upvotes", "").strip()
                        score = score.replace("\u2022", "")

                    # Get subreddit
                    subreddit_element = post.find("a", class_="post_subreddit")
                    subreddit = subreddit_element.get_text(strip=True) if subreddit_element else None

                    # Create post dictionary
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
    return random.choice(post_data)

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