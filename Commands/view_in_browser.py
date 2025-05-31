from Utils.utils import fetch_cmd_data, check_cooldown, is_url
import urllib.parse
import config

def reply_with_view_in_browser(self, message):
    try:
        github_site = config.GITHUB_SITE
        if not github_site:
            return

        cmd = fetch_cmd_data(self, message)

        if not check_cooldown(cmd.state, cmd.nick, cmd.cooldown):
            return
        
        if not cmd.params:
            self.send_privmsg(cmd.channel, f"{cmd.username} Please provide a URL to view in browser.")
            return

        url = cmd.params
        valid_url = is_url(url)
        
        if not valid_url:
            self.send_privmsg(cmd.channel, f"{cmd.username} Please provide a valid URL.")
            return
        
        encoded_url = urllib.parse.quote(url, safe=':/.')
        if not encoded_url:
            self.send_privmsg(cmd.channel, f"{cmd.username} Failed to encode URL.")
            return
        
        if len(encoded_url) > 495:
            self.send_privmsg(cmd.channel, f"{cmd.username} Encoded URL too long to send on Twitch.")
            return
        
        full_url = f"{github_site}?url={encoded_url}"
        
        self.send_privmsg(cmd.channel, full_url)

    except Exception as e:
        print(f"[Error] {e}")
        self.send_privmsg(cmd.channel, f"{cmd.username} Unexpected error occurred.")
