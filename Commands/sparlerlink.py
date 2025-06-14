import random, requests
from Utils.utils import check_cooldown, fetch_cmd_data, encode_str


def reply_with_sparlerlink(self, message):
    cmd = fetch_cmd_data(self, message)
    
    if not check_cooldown(cmd.state, cmd.nick, cmd.cooldown):
        return

    url = "https://pr0gramm.com/api/items/get?flags=1"
    
    if cmd.params:
        if "-p" in cmd.params:
            cmd.params = cmd.params[:cmd.params.index("-p")]
            url += "&promoted=1"

        url += f"&tags={encode_str(cmd.params)}"

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json().get('items', [])
        
        if len(data) < 1:
            self.send_privmsg(cmd.channel, "No link for @Sparler :(")
        else:
            random_item = data[random.randint(0, len(data) - 1)]
            text = f"https://vid.pr0gramm.com/{random_item['image']}"
            self.send_privmsg(cmd.channel, text)

    except Exception as e:
        print(e)
        self.send_privmsg(cmd.channel, "No link for @Sparler :( (something went wrong)")
