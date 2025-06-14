import requests, config
from Utils.utils import check_cooldown, fetch_cmd_data


def reply_with_suggest(self, message):
    cmd = fetch_cmd_data(self, message)
    
    if not check_cooldown(cmd.state, cmd.nick, cmd.cooldown):
        return
    
    headers = {
    'Authorization': f"Bearer {config.githubToken}",
    'Accept': 'application/vnd.github.v3+json'
        }
    
    body = {
            'title': cmd.params if cmd.params  else "No Title",
            'body': f"Suggestion from {cmd.nick} in #{cmd.channel}"
    }

    response = requests.post('https://api.github.com/repos/BluePigman/BluePagmanBot/issues', headers=headers, json=body)
    
    if response.status_code == 201:
            # created
        response = response.json()
        self.send_privmsg(cmd.channel, f"Suggestion created successfully under issue #{response['number']}: \
        {response['html_url']}")

    elif response.status_code == 400:
        # bad request
        self.send_privmsg(cmd.channel, f"Error {response.status_code}:Bad request.")

    elif response.status_code == 403:
        # forbidden
        self.send_privmsg(cmd.channel, f"Error {response.status_code}:Forbidden.")
    
    else:
        self.send_privmsg(cmd.channel, f"Error {response.status_code}.")