import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import time, config, requests

headers = {
            'Authorization': f"Bearer {config.user_access_token}",
            'Client-ID': f'{config.client_id}',
    }

def reload_emotes(self, message):
    if (message.user not in self.state or time.time() - self.state[message.user] > 30):
        self.state[message.user] = time.time()
        
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
            m = f"Emotes reloaded successfully in {elapsed_time:.2f} seconds. Random emote is: {random_emote}"
            self.send_privmsg(message.channel, m)
        else:
            # Print error message
            m = f"Error: {response.status_code} - {response.text}"
            self.send_privmsg(message.channel, m)