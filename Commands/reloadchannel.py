import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import requests, time, config

def reload_7tv_channel(self, message):
    if (message['source']['nick'] not in self.state or time.time() - self.state[message['source']['nick']] > self.cooldown):
        self.state[message['source']['nick']] = time.time()

        channel_id =  message["tags"]["room-id"]
        start_time = time.time()  # Start measuring time
        # Make GET request
        response = requests.get(f"https://7tv.io/v3/users/twitch/{channel_id}")

        if response.status_code == 200:
            # Handle successful response
            data = response.json()
            emotes = data["emote_set"]["emotes"]

            # Ensure the Emotes collection exists
            emotes_collection = self.db['Emotes']

            # Prepare batch insert
            new_emotes = []
            for emote in emotes:
                emote_id = emote["id"]
                name = emote["name"]
                url = "https://cdn.7tv.app/emote/" + emote_id + "/4x.webp"

                # Check if the emote already exists in the collection
                if not emotes_collection.find_one({"emote_id": emote_id}):
                    new_emotes.append({
                        "emote_id": emote_id,
                        "name": name,
                        "url": url
                    })

            # Batch insert new emotes
            if new_emotes:
                emotes_collection.insert_many(new_emotes)
            
            end_time = time.time()  # End measuring time
            elapsed_time = end_time - start_time  # Calculate elapsed time
            
            # Send success message with elapsed time
            m = f"7 TV Channel Emotes reloaded successfully in {elapsed_time:.2f} seconds."
            self.send_privmsg(message['command']['channel'], m)
        else:
            # Print error message
            m = f"Error: {response.status_code} - {response.text}"
            self.send_privmsg(message['command']['channel'], m)
        
def reload_ffz_channel(self, message):
    if (message['source']['nick'] not in self.state or time.time() - self.state[message['source']['nick']] > self.cooldown):
        self.state[message['source']['nick']] = time.time()

        channel_id =  get_user_id(message['command']['channel']) 
        if not channel_id:
            m = f"Error: Could not retrieve channel ID for {message['command']['channel']}"
            self.send_privmsg(message['command']['channel'], m)
            return
        start_time = time.time()  # Start measuring time
        # Make GET request
        response = requests.get(f"https://api.frankerfacez.com/v1/room/id/{channel_id}")

        if response.status_code == 200:
            # Handle successful response
            data = response.json()
            
            # Ensure the Emotes collection exists
            emotes_collection = self.db['Emotes']

            ffz_id = data["room"]["set"]
            # Prepare batch insert
            new_emotes = []
            for emote_set in data["sets"][str(ffz_id)]["emoticons"]:
                emote_id = "FFZ-" + str(emote_set['id'])
                name = emote_set['name']
                url = "https://cdn.frankerfacez.com/emote/" + str(emote_set['id']) + "/4"
                
                # Check if the emote already exists in the collection
                if not emotes_collection.find_one({"emote_id": emote_id}):
                    new_emotes.append({
                        "emote_id": emote_id,
                        "name": name,
                        "url": url
                    })

            # Batch insert new emotes
            if new_emotes:
                emotes_collection.insert_many(new_emotes)
            
            end_time = time.time()  # End measuring time
            elapsed_time = end_time - start_time  # Calculate elapsed time
            
            # Send success message with elapsed time
            m = f"FFZ Channel Emotes reloaded successfully in {elapsed_time:.2f} seconds."
            self.send_privmsg(message['command']['channel'], m)
        else:
            # Print error message
            m = f"Error: {response.status_code} - {response.text}"
            self.send_privmsg(message['command']['channel'], m)

def reload_bttv_channel(self, message):
    if (message['source']['nick'] not in self.state or time.time() - self.state[message['source']['nick']] > self.cooldown):
        self.state[message['source']['nick']] = time.time()

        channel_id =  get_user_id(message['command']['channel']) 
        if not channel_id:
            m = f"Error: Could not retrieve channel ID for {message['command']['channel']}"
            self.send_privmsg(message['command']['channel'], m)
            return
        start_time = time.time()  # Start measuring time
        # Make GET request
        response = requests.get(f"https://api.betterttv.net/3/cached/users/twitch/{channel_id}")

        if response.status_code == 200:
            # Handle successful response
            data = response.json()
            emotes_list = data["channelEmotes"] + data["sharedEmotes"]
            # Ensure the Emotes collection exists
            emotes_collection = self.db['Emotes']

            # Prepare batch insert
            new_emotes = []
            for emote in emotes_list:
                emote_id = emote["id"]
                name = emote["code"]
                url = "https://cdn.betterttv.net/emote/" + emote_id + "/3x"
                
                # Check if the emote already exists in the collection
                if not emotes_collection.find_one({"emote_id": emote_id}):
                    new_emotes.append({
                        "emote_id": emote_id,
                        "name": name,
                        "url": url
                    })

            # Batch insert new emotes
            if new_emotes:
                emotes_collection.insert_many(new_emotes)
            
            end_time = time.time()  # End measuring time
            elapsed_time = end_time - start_time  # Calculate elapsed time
            
            # Send success message with elapsed time
            m = f"BetterTTV Channel Emotes reloaded successfully in {elapsed_time:.2f} seconds."
            self.send_privmsg(message['command']['channel'], m)
        else:
            self.send_privmsg(message['command']['channel'], f"Error: {response.status_code} - {response.text}")

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