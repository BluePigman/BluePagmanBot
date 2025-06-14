import pymongo
import requests
import time
from Utils.utils import check_cooldown, fetch_cmd_data

def reload_channel(self, message):
    cmd = fetch_cmd_data(self, message)
    if not check_cooldown(cmd.state, cmd.nick, cmd.cooldown): 
        return
    
    channel_id = message["tags"]["room-id"]
    start_time = time.time()


    emotes_collection = self.db['Emotes']
    channel_emotes_collection = self.db['ChannelEmotes']
    bulk_emote_operations = []
    bulk_channel_operations = []

    existing_emotes = channel_emotes_collection.find({"channel_id": channel_id})
    existing_emote_ids = {emote["emote_id"] for emote in existing_emotes} # all emote ids before the reload.

    # Combined current emote set for all platforms, will be filled in with emotes fetched from reload.
    current_emote_ids = set()

    # Helper function to process emotes from different platforms
    def process_emotes(emotes, emote_type, id_key="id", name_key="name", url_template=""):
        for emote in emotes:
            emote_id = emote[id_key]
            name = emote[name_key]
            url = url_template.format(emote_id)

            # Upsert emote in the Emotes collection
            bulk_emote_operations.append(
                pymongo.UpdateOne(
                    {"emote_id": emote_id},
                    {"$set": {"name": name, "url": url, "emote_type": emote_type}},
                    upsert=True
                )
            )
            current_emote_ids.add(emote_id)

            # Upsert channel-emote relationship (if no document found then add it)
            bulk_channel_operations.append(
                pymongo.UpdateOne(
                    {"channel_id": channel_id, "emote_id": emote_id},
                    {"$set": {"channel_id": channel_id, "emote_id": emote_id}},
                    upsert=True
                )
            )

    # 7TV emotes
    response = requests.get(f"https://7tv.io/v3/users/twitch/{channel_id}")
    if response.status_code == 200:
        data = response.json()
        emotes = data["emote_set"]["emotes"]
        process_emotes(emotes, "7TV", "id", "name",
                        "https://cdn.7tv.app/emote/{}/4x.webp")

    # FFZ emotes
    response = requests.get(
        f"https://api.frankerfacez.com/v1/room/id/{channel_id}")
    if response.status_code == 200:
        data = response.json()
        ffz_id = data["room"]["set"]
        emotes = data["sets"][str(ffz_id)]["emoticons"]
        process_emotes(emotes, "FFZ", "id", "name",
                        "https://cdn.frankerfacez.com/emote/{}/4")

    # BTTV emotes
    response = requests.get(
        f"https://api.betterttv.net/3/cached/users/twitch/{channel_id}")
    if response.status_code == 200:
        data = response.json()
        emotes = data["channelEmotes"] + data["sharedEmotes"]
        process_emotes(emotes, "BTTV", "id", "code",
                        "https://cdn.betterttv.net/emote/{}/3x")

    # Execute bulk upserts for emotes and channel emotes
    if bulk_emote_operations:
        emotes_collection.bulk_write(bulk_emote_operations)
    if bulk_channel_operations:
        channel_emotes_collection.bulk_write(bulk_channel_operations)

    # Perform deletions for outdated emotes
    to_delete = existing_emote_ids - current_emote_ids
    if to_delete:
        channel_emotes_collection.delete_many({"channel_id": channel_id, "emote_id": {"$in": list(to_delete)}})

    end_time = time.time()
    elapsed_time = end_time - start_time
    self.send_privmsg(message['command']['channel'],
                        f"Channel emotes reloaded successfully in {elapsed_time:.2f} seconds.")