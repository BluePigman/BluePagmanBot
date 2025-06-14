import config, requests
from Utils.utils import check_cooldown, fetch_cmd_data, clean_str

def reply_with_timeout(self, message):
    cmd = fetch_cmd_data(self, message)

    if not check_cooldown(cmd.state, cmd.nick, cmd.cooldown):
        return

    if not cmd.params:
        self.send_privmsg(cmd.channel, f"{cmd.username}, please specify a user (not moderator or broadcaster) to timeout.")
        return

    if cmd.params.lower() == "amount":
        user_data = self.users.find_one({'user': cmd.nick})
        count = user_data.get('timeout', 0) if user_data else 0
        self.send_privmsg(cmd.channel, f"{cmd.username}, you have {count} timeouts available.")
        return

    user_to_timeout = clean_str(cmd.params, ["@", ","])

    # Validate timeout ownership
    user_data = self.users.find_one({'user': cmd.nick})
    timeout_count = user_data.get('timeout', 0) if user_data else 0

    if timeout_count == 0:
        m = f"{cmd.username}, you don't have any timeouts to use. Buy them in the shop with {self.prefix}shop buy timeout."
        self.send_privmsg(cmd.channel, m)
        return

    # Get user IDs
    channel_id = message["tags"]["room-id"]
    timeout_id = get_user_id(user_to_timeout)
    moderator_id = get_user_id('bluepagmanbot')

    # Attempt timeout
    result = timeout(channel_id, moderator_id, timeout_id)

    if result == "Success":
        self.users.update_one({'user': cmd.nick}, {'$inc': {'timeout': -1}})
    else:
        responses = {
            "Bad": f"Timeout failed, either the user is a mod/broadcaster or the user does not exist.",
            "InsufficientPrivileges": "The bot is not a moderator in this channel!",
        }
        fallback = f"{cmd.username}, something went wrong. Your timeout was not used."
        self.send_privmsg(cmd.channel, responses.get(result, fallback))


def get_user_id(username):
    headers = {
            'Authorization': f"Bearer {config.user_access_token}",
            'Client-ID': f'{config.client_id}',
        }
    
    params = {
        'login': username,
    }

    response = requests.get('https://api.twitch.tv/helix/users', headers=headers, params=params)

    if response.status_code == 200:
        data = response.json()
        if data['data']:
            user_info = data['data'][0]
            user_id = user_info['id']
            return user_id
        else:
            return None
    else:
        return None

def timeout(channel, moderator, user):
    """Attempt a POST request to timeout a user"""

    headers = {
            'Authorization': f"Bearer {config.user_access_token}",
            'Client-ID': f'{config.client_id}',
    }

    params = {
        'broadcaster_id': channel,
        'moderator_id': moderator,
    }

    body = {
        'data': {
            'user_id': user,
            'duration': 10,
            'reason': "Someone bought the timeout in the shop and used it on you!"
        }
    }
    
    response = requests.post('https://api.twitch.tv/helix/moderation/bans', headers=headers, params=params, json=body)

    if response.status_code == 200:
        print(f"{user} timed out successfully in #{channel}!")
        return "Success"
    if response.status_code == 400:
        print("User could not be timed out!")
        return "Bad"
    if response.status_code == 401:
        print("Token is invalid!")
        return "TokenError"
    if response.status_code == 403:
        print("The bot is not a moderator!")
        return "InsufficientPrivileges"
    else:
        print("Request failed with status code:", response.status_code)
        return "Fail"