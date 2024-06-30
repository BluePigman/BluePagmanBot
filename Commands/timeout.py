import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))



import time, config, requests

def reply_with_timeout(self, message):
    if (message['source']['nick'] not in self.state or time.time() - self.state[message['source']['nick']] >
            self.cooldown):
        self.state[message['source']['nick']] = time.time()

        if not message['command']['botCommandParams']:
            m = f"@{message['source']['nick']}, please specify a user (not moderator or broadcaster) to timeout."
            self.send_privmsg(message['command']['channel'], m)
            return

        userToTimeout = message['command']['botCommandParams']

        if '\U000e0000' in userToTimeout:
            userToTimeout = userToTimeout.replace('\U000e0000', '')

        user_data = self.users.find_one({'user': message['source']['nick']})
        if not user_data or 'timeout' not in user_data:
            m = f"@{message['source']['nick']}, you don't have any timeouts to use. Buy them in the shop."
            self.send_privmsg(message['command']['channel'], m)
            return

        timeout_count = user_data['timeout']
        if timeout_count <= 0:
            m = f"@{message['source']['nick']}, you don't have any timeouts left to use. Buy them in the shop."
            self.send_privmsg(message['command']['channel'], m)
            return

        if ',' in userToTimeout:
            userToTimeout = userToTimeout.replace(',', '')
        if '@' in userToTimeout:
            userToTimeout = userToTimeout.replace('@', '')

        
        if message['command']['botCommandParams'][0] == 'amount':
            m = f"@{message['source']['nick']}, you have {timeout_count} timeouts available."
            self.send_privmsg(message['command']['channel'], m)
            return

        # Get user ID of the channel and user to timeout
        channel_id  = get_user_id(message['command']['channel'])
        timeout_id = get_user_id(userToTimeout)
        moderator_id = get_user_id('bluepagmanbot')

        m = f"@{message['source']['nick']} used a timeout on {userToTimeout}!"
        self.send_privmsg(message['command']['channel'], m)

        # Attempt timeout
        result = timeout(channel_id, moderator_id, timeout_id)

        if result == "Success":
            self.users.update_one({'user': message['source']['nick']}, {'$inc': {'timeout': -1}})
            return
        if result == "Bad":
            self.users.update_one({'user': message['source']['nick']}, {'$inc': {'timeout': -1}})
            m = f"@{message['source']['nick']}, you tried to timeout a mod/broadcaster, which is impossible. -500 LUL"
            self.send_privmsg(message['command']['channel'], m)
            return
        if result == "InsufficientPrivileges":
            m = "The bot is not a moderator in this channel!"
            self.send(message['command']['channel'], m)
            return
        else:
            m = f"@{message['source']['nick']}, something went wrong. Your timeout was not used."
            self.send_privmsg(message['command']['channel'], m)
            return 


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
        # Handle successful response
        data = response.json()
        if data['data']:
            user_info = data['data'][0]
            user_id = user_info['id']
            return user_id
        else:
            return None
    else:
        # Handle error response
        return None

def timeout(channel, moderator, user):
    # Construct headers
    headers = {
            'Authorization': f"Bearer {config.user_access_token}",
            'Client-ID': f'{config.client_id}',
    }

    # Construct request parameters
    params = {
        'broadcaster_id': channel,
        'moderator_id': moderator,
    }

    # Construct request body
    body = {
        'data': {
            'user_id': user,
            'duration': 10,
            'reason': "Someone bought the timeout in the shop and used it on you!"
        }
    }

    # Make POST request to carry out the timeout
    response = requests.post('https://api.twitch.tv/helix/moderation/bans', headers=headers, params=params, json=body)

     # Check response status code
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