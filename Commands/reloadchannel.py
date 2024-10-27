import pymongo
import requests
import time

def reload_channel(self, message):
    if (message['source']['nick'] not in self.state or
            time.time() - self.state[message['source']['nick']] > self.cooldown):
        self.state[message['source']['nick']] = time.time()

        channel_id = message["tags"]["room-id"]
        start_time = time.time()

        emotes_collection = self.db['Emotes']
        channel_emotes_collection = self.db['ChannelEmotes']

        # Set to track all new emote IDs across platforms for this channel
        all_new_emote_ids = set()

        # Function to sync emotes for a specific platform
        def sync_platform_emotes(emotes, emote_type, url_template, id_key="id", name_key="name"):
            new_emote_details = []
            new_channel_emote_relations = []
            new_emote_ids = set()

            for emote in emotes:
                emote_id = emote[id_key]
                name = emote[name_key]
                url = url_template.format(emote_id)

                new_emote_ids.add(emote_id)
                all_new_emote_ids.add(emote_id)

                new_emote_details.append(
                    pymongo.UpdateOne(
                        {"emote_id": emote_id},
                        {"$set": {"name": name, "url": url, "emote_type": emote_type}},
                        upsert=True
                    )
                )
                new_channel_emote_relations.append(
                    pymongo.UpdateOne(
                        {"channel_id": channel_id, "emote_id": emote_id},
                        {"$set": {"channel_id": channel_id, "emote_id": emote_id, "emote_type": emote_type}},
                        upsert=True
                    )
                )

            if new_emote_details:
                emotes_collection.bulk_write(new_emote_details)
            if new_channel_emote_relations:
                channel_emotes_collection.bulk_write(new_channel_emote_relations)

        # Fetch and sync emotes for 7TV
        response = requests.get(f"https://7tv.io/v3/users/twitch/{channel_id}")
        if response.status_code == 200:
            data = response.json()
            emotes = data["emote_set"]["emotes"]
            sync_platform_emotes(emotes, "7TV", "https://cdn.7tv.app/emote/{}/4x.webp")

        # Fetch and sync emotes for FFZ
        response = requests.get(f"https://api.frankerfacez.com/v1/room/id/{channel_id}")
        if response.status_code == 200:
            data = response.json()
            ffz_id = data["room"]["set"]
            emotes = data["sets"][str(ffz_id)]["emoticons"]
            sync_platform_emotes(emotes, "FFZ", "https://cdn.frankerfacez.com/emote/{}/4")

        # Fetch and sync emotes for BTTV
        response = requests.get(f"https://api.betterttv.net/3/cached/users/twitch/{channel_id}")
        if response.status_code == 200:
            data = response.json()
            emotes = data["channelEmotes"] + data["sharedEmotes"]
            sync_platform_emotes(emotes, "BTTV", "https://cdn.betterttv.net/emote/{}/3x", "id", "code")

        # Delete emotes no longer in the new set, excluding global Twitch emotes
        channel_emotes_collection.delete_many(
            {"channel_id": channel_id, "emote_id": {"$nin": list(all_new_emote_ids)}}
        )
        emotes_collection.delete_many(
            {"emote_id": {"$nin": list(all_new_emote_ids)}, "emote_type": {"$ne": "Twitch"}}
        )

        end_time = time.time()
        elapsed_time = end_time - start_time
        self.send_privmsg(message['command']['channel'],
                          f"Channel emotes reloaded successfully in {elapsed_time:.2f} seconds.")
