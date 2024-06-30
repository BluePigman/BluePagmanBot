import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import requests, time, random, config

headers = {
            'Authorization': f"Bearer {config.user_access_token}",
            'Client-ID': f'{config.client_id}',
    }

def reload_global_emotes(self, message):
    if (message['source']['nick'] not in self.state or time.time() - self.state[message['source']['nick']] > self.cooldown):
        self.state[message['source']['nick']] = time.time()
        reload_7tv_global(self, message)
        reload_ffz_global(self, message)
        reload_bttv_global(self, message)
        reload_twitch_global(self, message)
        self.send_privmsg(message['command']['channel'], "Global Emotes reloaded successfully.")

def reload_twitch_global(self, message):
    if (message['source']['nick'] not in self.state or time.time() - self.state[message['source']['nick']] > self.cooldown):
        self.state[message['source']['nick']] = time.time()
        
        start_time = time.time()  # Start measuring time

        # Make GET request
        response = requests.get('https://api.twitch.tv/helix/chat/emotes/global', headers=headers)

        if response.status_code == 200:
            # Handle successful response
            data = response.json()
            
            # Ensure the Emotes collection exists
            emotes_collection = self.db['Emotes']

            # Create an index on emote_id if it doesn't exist
            emotes_collection.create_index('emote_id', unique=True)

            # Prepare batch insert
            new_emotes = []
            for emote in data['data']:
                emote_id = emote['id']
                name = emote['name']
                url = emote['images']['url_4x']
                
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

            # Get a random emote from the collection
            random_emote = emotes_collection.aggregate([{'$sample': {'size': 1}}])
            random_emote = next(random_emote)['name']
            
            end_time = time.time()  # End measuring time
            elapsed_time = end_time - start_time  # Calculate elapsed time
            
            # Send success message with elapsed time
            m = f"Global Twitch emotes reloaded successfully in {elapsed_time:.2f} seconds. Random emote is: {random_emote}"
            self.send_privmsg(message['command']['channel'], m)
        else:
            # Print error message
            m = f"Error: {response.status_code} - {response.text}"
            self.send_privmsg(message['command']['channel'], m)

def reload_bttv_global(self, message):
    start_time = time.time()  # Start measuring time
    # Make GET request
    response = requests.get('https://api.betterttv.net/3/cached/emotes/global')

    if response.status_code == 200:
        # Handle successful response
        data = response.json()
        
        # Ensure the Emotes collection exists
        emotes_collection = self.db['Emotes']


        # Prepare batch insert
        new_emotes = []
        for emote_set in data:
            emote_id = emote_set['id']
            name = emote_set['code']
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
        m = f"Global BetterTTV emotes reloaded successfully in {elapsed_time:.2f} seconds."
        self.send_privmsg(message['command']['channel'], m)
    else:
        # Print error message
        m = f"Error: {response.status_code} - {response.text}"
        self.send_privmsg(message['command']['channel'], m)


def reload_ffz_global(self, message):
    start_time = time.time()  # Start measuring time
    # Make GET request
    response = requests.get('https://api.frankerfacez.com/v1/set/global/ids')

    if response.status_code == 200:
        # Handle successful response
        data = response.json()
        
        # Ensure the Emotes collection exists
        emotes_collection = self.db['Emotes']

        # Prepare batch insert
        new_emotes = []
        for emote_set in data["sets"]["3"]["emoticons"]:
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
        m = f"FFZ Global Emotes reloaded successfully in {elapsed_time:.2f} seconds."
        self.send_privmsg(message['command']['channel'], m)
    else:
        # Print error message
        m = f"Error: {response.status_code} - {response.text}"
        self.send_privmsg(message['command']['channel'], m)

def reload_7tv_global(self, message):
    start_time = time.time()  # Start measuring time
    # Make GET request
    response = requests.get("https://7tv.io/v3/emote-sets/global")

    if response.status_code == 200:
        # Handle successful response
        data = response.json()
        
        # Ensure the Emotes collection exists
        emotes_collection = self.db['Emotes']

        # Prepare batch insert
        new_emotes = []
        for emote_set in data["emotes"]:
            emote_id = emote_set["id"]
            name = emote_set['name']
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
        m = f"7TV Global Emotes reloaded successfully in {elapsed_time:.2f} seconds."
        self.send_privmsg(message['command']['channel'], m)
    else:
        # Print error message
        m = f"Error: {response.status_code} - {response.text}"
        self.send_privmsg(message['command']['channel'], m)