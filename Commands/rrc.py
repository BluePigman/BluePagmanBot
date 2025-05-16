import random
import html
import requests
from utils import (
    proxy_get_request,
    clean_str,
    send_chunks,
    fetch_cmd_data,
    check_cooldown,
    parse_str,
)

MAX_COMMENTS = 300

base_urls = {
    "hot_posts": "https://www.reddit.com/r/{subreddit}/hot.json?limit=30",
    "comments": "https://www.reddit.com/comments/{post_id}.json?depth=10&limit={MAX_COMMENTS}"
}

def get_posts(subreddit, max_comments=MAX_COMMENTS):
    url = base_urls["hot_posts"].format(subreddit=subreddit)

    try:
        res = proxy_get_request(url)
    except requests.RequestException as e:
        print(f"[get_posts] Request failed: {e}")
        return {"success": False, "message": "Network error while fetching posts."}

    print(f"[get_posts] HTTP {res.status_code} for subreddit {subreddit}")
    if res.status_code != 200:
        msg = f"Failed to get posts for /r/{subreddit}"
        print(f"[get_posts] {msg}")
        return {"success": False, "message": msg}

    all_posts = res.json().get('data', {}).get('children', [])
    if not all_posts:
        msg = f"Subreddit /r/{subreddit} not found or empty."
        print(f"[get_posts] {msg}")
        return {"success": False, "message": msg}

    posts_with_comments = []
    for p in all_posts:
        num_comments = p['data'].get('num_comments', 0)

        if num_comments < 1:
            continue
        if num_comments > max_comments:
            continue

        posts_with_comments.append(p)

    if not posts_with_comments:
        msg = f"Could not find posts with comments in /r/{subreddit}"
        print(f"[get_posts] {msg}")
        return {"success": False, "message": msg}

    return {"success": True, "posts_data": posts_with_comments}

def get_random_comment(posts, subreddit, min_words=15):
    random_post = random.choice(posts)['data']
    post_id = random_post['id']

    url = base_urls["comments"].format(post_id=post_id, MAX_COMMENTS=MAX_COMMENTS)

    try:
        res = proxy_get_request(url)
    except requests.RequestException as e:
        print(f"[get_random_comment] Request failed: {e}")
        return {"success": False, "message": "Network error while fetching comments."}

    print(f"[get_random_comment] HTTP {res.status_code} for post {post_id}")
    if res.status_code != 200:
        msg = f"Failed to get comments from post"
        print(f"[get_random_comment] {msg}")
        return {"success": False, "message": msg}

    items = res.json()
    if len(items) < 2:
        print(f"[get_random_comment] Unexpected response structure for post {post_id}")
        return {"success": False, "message": "Failed to get comments from post"}

    comments = items[1]['data'].get('children', [])
    all_comments = []

    while comments:
        comment = comments.pop()
        comment_info = comment['data']
        all_comments.append(comment_info)
        replies = comment_info.get('replies', None)
        if replies and isinstance(replies, dict):
            replies_data = replies.get('data', {}).get('children', [])
            comments.extend(replies_data)

    print(f"[get_random_comment] Total comments (including replies): {len(all_comments)}")

    filtered_comments = [
        c for c in all_comments
        if c.get('body') not in ('[removed]',) and c.get('author') != 'AutoModerator' and 'body' in c
    ]
    
    # Give full weight to comments above min_words + higher score
    weights = []
    for c in filtered_comments:
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

    random_comment = random.choices(filtered_comments, weights=weights, k=1)[0]

    post_link = f"https://www.reddit.com{random_post['permalink']}"
    comment_link = f"https://www.reddit.com/r/{subreddit}/comments/{post_id}/comment/{random_comment['id']}"
    alt_comment_link = f"https://www.reddit.com{random_comment['permalink']}"

    comment_body_html = random_comment['body_html']
    comment_body = html.unescape(comment_body_html)
    comment_body_clean = parse_str(comment_body, "html").get_text()

    return {
        "success": True,
        "post_link": post_link,
        "comment_body": comment_body_clean,
        "comment_link": comment_link or alt_comment_link
    }

def reply_with_random_reddit_comment(self, message):
    cmd_data = fetch_cmd_data(self, message)
    username, channel, params, nick, state, cooldown = cmd_data.values()

    check_cooldown(state, nick, cooldown)

    if not params:
        self.send_privmsg(channel, f"{username} Please provide a subreddit name to get a random comment from.")
        return

    try:
        subreddit = params.strip()
        posts_result = get_posts(subreddit)

        if not posts_result.get("success"):
            self.send_privmsg(channel, f"{username} {posts_result['message']}")
            return

        random_comment_result = get_random_comment(posts_result["posts_data"], subreddit)

        if not random_comment_result.get("success"):
            self.send_privmsg(channel, f"{username} {random_comment_result['message']}")
            return

        m = f"{random_comment_result['comment_body']} {random_comment_result['comment_link']}"
        send_chunks(self.send_privmsg, channel, clean_str(m))

    except Exception as e:
        print(f"[reply_with_random_reddit_comment] Error: {e}")
        self.send_privmsg(channel, f"{username} Failed to get a random comment.")
