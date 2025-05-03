import requests
import random
import html
import config


base_urls = {
    "top_posts": "https://www.reddit.com/r/{subreddit}/top.json?t=day&limit=15",
    "comments": "https://www.reddit.com/comments/{post_id}.json"
}

def get_top_posts(subreddit):
    if config.PROXY:
        req = requests.get(config.PROXY, headers={"url": base_urls["top_posts"].format(subreddit=subreddit), 'User-agent': 'BluePagmanBot'})
    else:
        req = requests.get(base_urls["top_posts"].format(subreddit=subreddit))

    req.raise_for_status()
    posts = req.json()['data']['children']
    return posts if posts else []

def get_comments(post_id):
    if config.PROXY:
        res = requests.get(config.PROXY, headers={"url": base_urls["comments"].format(post_id=post_id), 'User-agent': 'BluePagmanBot'})
    else:
        res = requests.get(base_urls["comments"].format(post_id=post_id))

    res.raise_for_status()
    comments = res.json()[1]['data']['children']
    comments = [c['data'] for c in comments if c['kind'] == 't1']
    return comments if comments else []

def get_random_comment(subreddit, min_words=15):
    try:
        posts = get_top_posts(subreddit)
        if not posts:
            return None

        random_post = random.choice(posts)['data']
        post_id = random_post['id']

        comments = get_comments(post_id)
        if not comments:
            return None

        comments = [c for c in comments if c['body'] != '[removed]' and c['author'] != 'AutoModerator']

        # Give full weight to comments above min_words + higher score
        weights = []
        for c in comments:
            word_count = len(c['body'].split())
            score = max(c.get('score', 1), 1)
            if word_count >= min_words:
                word_bonus = 1.0
            else:
                distance = min_words - word_count
                penalty = (distance ** 2) * 0.01  # penalty grows quadratically
                word_bonus = max(0.1, 1 - penalty)

            weight = (score + 1) * word_bonus
            weights.append(weight)

        random_comment = random.choices(comments, weights=weights, k=1)[0]

        post_link = f"https://www.reddit.com{random_post['permalink']}"
        comment_link = f"https://www.reddit.com/r/{subreddit}/comments/{post_id}/comment/{random_comment['id']}"
        comment_body = html.unescape(random_comment['body'])
        
        return {'post_link': post_link, 'comment_body': comment_body, 'comment_link': comment_link}

    except Exception as e:
        return None

def reply_with_random_reddit_comment(self, message):
    username = f"@{message['tags']['display-name']}"
    channel = message['command']['channel']
    params = message['command']['botCommandParams']

    if not params:
        self.send_privmsg(channel, f"{username} Please provide a subreddit name to get a random comment from.")
        return

    try:
        subreddit = params.strip()
        result = get_random_comment(subreddit)

        if not result:
            self.send_privmsg(channel, f"{username} No posts or comments found in /r/{subreddit}.")
            return

        comment_link = result['comment_link']
        comment_body = result['comment_body']

        m = f"{comment_body}; {comment_link}"
        self.send_privmsg(channel, m)

    except Exception:
        self.send_privmsg(channel, f"{username}, failed to get a random comment.")

