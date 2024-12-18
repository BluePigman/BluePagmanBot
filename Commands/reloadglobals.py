import config
import time
import requests

headers = {
    'Authorization': f"Bearer {config.user_access_token}",
    'Client-ID': f'{config.client_id}',
}


def reload_global_emotes(self, message):
    if (message['source']['nick'] not in self.state or time.time() - self.state[message['source']['nick']] > self.cooldown):
        self.state[message['source']['nick']] = time.time()
        reload_7tv_global(self, message)
        time.sleep(1.1)
        reload_ffz_global(self, message)
        time.sleep(1.1)
        reload_bttv_global(self, message)
        time.sleep(1.1)
        reload_twitch_global(self, message)
        time.sleep(1.1)
        self.send_privmsg(message['command']['channel'],
                          "Global Emotes reloaded successfully.")


def reload_twitch_global(self, message):
    start_time = time.time()
    response = requests.get(
        'https://api.twitch.tv/helix/chat/emotes/global', headers=headers)

    if response.status_code == 200:
        data = response.json()
        emotes_collection = self.db['Emotes']
        new_emotes = []

        for emote in data['data']:
            emote_id = emote['id']
            name = emote['name']
            url = emote['images']['url_4x']

            # Check if emote with the same emote_id and type already exists
            if not emotes_collection.find_one({"emote_id": emote_id, "emote_type": "Twitch"}):
                new_emotes.append({
                    "emote_id": emote_id,
                    "name": name,
                    "url": url,
                    "emote_type": "Twitch",
                    "is_global": True
                })

        if new_emotes:
            emotes_collection.insert_many(new_emotes)

        random_emote = emotes_collection.aggregate(
            [{'$match': {"emote_type": "Twitch"}}, {'$sample': {'size': 1}}])
        random_emote = next(random_emote)['name']

        elapsed_time = time.time() - start_time
        m = f"Global Twitch emotes reloaded successfully in {elapsed_time:.2f} seconds. Random emote is: {random_emote}"
        self.send_privmsg(message['command']['channel'], m)
    else:
        m = f"Error: {response.status_code} - {response.text}"
        self.send_privmsg(message['command']['channel'], m)


def reload_bttv_global(self, message):
    start_time = time.time()
    response = requests.get('https://api.betterttv.net/3/cached/emotes/global')

    if response.status_code == 200:
        data = response.json()
        emotes_collection = self.db['Emotes']
        new_emotes = []

        for emote_set in data:
            emote_id = emote_set['id']
            name = emote_set['code']
            url = f"https://cdn.betterttv.net/emote/{emote_id}/3x"

            if not emotes_collection.find_one({"emote_id": emote_id, "emote_type": "BTTV"}):
                new_emotes.append({
                    "emote_id": emote_id,
                    "name": name,
                    "url": url,
                    "emote_type": "BTTV",
                    "is_global": True
                })

        if new_emotes:
            emotes_collection.insert_many(new_emotes)

        elapsed_time = time.time() - start_time
        m = f"Global BTTV emotes reloaded successfully in {elapsed_time:.2f} seconds."
        self.send_privmsg(message['command']['channel'], m)
    else:
        m = f"Error: {response.status_code} - {response.text}"
        self.send_privmsg(message['command']['channel'], m)


def reload_ffz_global(self, message):
    start_time = time.time()
    response = requests.get('https://api.frankerfacez.com/v1/set/global/ids')

    if response.status_code == 200:
        data = response.json()
        emotes_collection = self.db['Emotes']
        new_emotes = []

        for emote_set in data["sets"]["3"]["emoticons"]:
            emote_id = f"FFZ-{emote_set['id']}"
            name = emote_set['name']
            url = f"https://cdn.frankerfacez.com/emote/{emote_set['id']}/4"

            if not emotes_collection.find_one({"emote_id": emote_id}):
                new_emotes.append({
                    "emote_id": emote_id,
                    "name": name,
                    "url": url,
                    "emote_type": "FFZ",
                    "is_global": True
                })
        if new_emotes:
            emotes_collection.insert_many(new_emotes)

        elapsed_time = time.time() - start_time
        m = f"FFZ Global Emotes reloaded successfully in {elapsed_time:.2f} seconds."
        self.send_privmsg(message['command']['channel'], m)
    else:
        m = f"Error: {response.status_code} - {response.text}"
        self.send_privmsg(message['command']['channel'], m)


def reload_7tv_global(self, message):
    start_time = time.time()
    response = requests.get("https://7tv.io/v3/emote-sets/global")

    if response.status_code == 200:
        data = response.json()
        emotes_collection = self.db['Emotes']
        new_emotes = []

        for emote_set in data["emotes"]:
            emote_id = emote_set["id"]
            name = emote_set['name']
            url = f"https://cdn.7tv.app/emote/{emote_id}/4x.webp"

            if not emotes_collection.find_one({"emote_id": emote_id, "emote_type": "7TV"}):
                new_emotes.append({
                    "emote_id": emote_id,
                    "name": name,
                    "url": url,
                    "emote_type": "7TV",
                    "is_global": True
                })

        if new_emotes:
            emotes_collection.insert_many(new_emotes)

        elapsed_time = time.time() - start_time
        m = f"7TV Global Emotes reloaded successfully in {elapsed_time:.2f} seconds."
        self.send_privmsg(message['command']['channel'], m)
    else:
        m = f"Error: {response.status_code} - {response.text}"
        self.send_privmsg(message['command']['channel'], m)
