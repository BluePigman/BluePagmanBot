import re

def convert_instagram_link(link):
  link = link.replace("instagram.com", "imginn.com")
  match = re.search(r'(?:/p/|/reel/)([^/?]+)', link)
  return f"https://imginn.com/p/{match.group(1)}/" if match else link
