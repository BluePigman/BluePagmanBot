import re

def convert_instagram_link(link):
    # Replace "instagram.com" with "imginn.com"
    link = link.replace("instagram.com", "imginn.com")
    
    # Use regex to identify and handle different link formats
    match = re.search(r'(?:/p/|/reel/)([^/?]+)', link)
    if match:
        post_id = match.group(1)
        # Construct the Imginn link with just the post ID
        imginn_link = f"https://imginn.com/p/{post_id}/"
        return imginn_link
    else:
        # Return the original link if it doesn't match expected patterns
        return link