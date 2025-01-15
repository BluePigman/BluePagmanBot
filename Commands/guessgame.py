import io
import random
import time
from threading import Timer

import requests
from Commands import gemini, describe, ascii
from PIL import Image


def reply_with_guess(self, message):
    """
    Manages the emote guessing game, handling game initialization, user guesses, and game progression.
    
    Handles multiple game scenarios:
    - Initializing a new game with configurable rounds and emote sources
    - Processing user guesses for the current emote
    - Tracking game state and managing rounds
    - Supporting global or channel-specific emote selection
    
    Parameters:
        message (dict): Twitch chat message containing game command and metadata
    
    Behavior:
        - Starts a new game if no active game exists
        - Allows configuring game rounds (1-4) and emote source (global/channel)
        - Validates user guesses against current emote
        - Rewards correct guesses with points
        - Manages game progression and termination
        - Implements cooldown mechanism to prevent rapid command triggering
    
    Raises:
        Handles potential errors in emote retrieval and game initialization internally
    """
    if (message['source']['nick'] not in self.state or time.time() - self.state[message['source']['nick']] > 0.4):
        self.state[message['source']['nick']] = time.time()
        channel_id = message["tags"]["room-id"]

        if not self.guessGameActive:
            # Start the game
            self.guessGameActive = True
            self.numRounds = 5
            is_global = False

            # Check if the user wants global emotes or number to specify rounds (1 - 4)
            if message['command']['botCommandParams']:
                params = message['command']['botCommandParams']
                if "global" in params:
                    is_global = True
                
                if params.isdigit() and int(params) < 5 and int(params) > 0:
                    self.numRounds = int(params)

            # Fetch emotes (either from channel or globally)
            emotes_list = get_random_emotes(
                self, channel_id, self.numRounds, is_global)

            if not emotes_list:
                self.send_privmsg(message['command']
                                  ['channel'], "No emotes found!")
                self.guessGameActive = False
                return

            if len(emotes_list) < self.numRounds:
                self.numRounds = len(emotes_list)
            mode = "Global Emotes" if is_global else "Channel Emotes"

            self.send_privmsg(
                message['command']['channel'], f"Game started! Mode is {mode}")
            self.gameEmotes = emotes_list
            # start a timer for 40s, if no one guesses emote in time, then reveal the emote.
            currentEmote = self.gameEmotes[self.currentRound]
            print(self.gameEmotes)
            start_new_round(self, message['command']['channel'])
            return

        # users will guess emotes using <guess EMOTE_NAME
        if not message['command']['botCommandParams']:
            return
        guess = message['command']['botCommandParams']

        currentEmote = self.gameEmotes[self.currentRound]
        if guess == currentEmote:
            # stop the timer
            self.guessGameRoundTimer.cancel()
            if self.hintTimer:
                self.hintTimer.cancel()

            # user guessed emote right, move to next round
            self.send_privmsg(
                message['command']['channel'], f"{message['tags']['display-name']} guessed it right! (+ 25 Pigga Coins) It's {currentEmote}")
            reward(self, message)
            time.sleep(1.1)
            if is_game_over(self.currentRound, self.numRounds):
                # end the game
                self.send_privmsg(message['command']['channel'], "Game has ended.")
                reset_game(self)
                return
            self.currentRound += 1
            start_new_round(self, message['command']['channel'])


def start_new_round(self, channel):
    """
    Starts a new round of the emote guessing game for a specific channel.
    
    This method handles the initialization of a new game round by:
    1. Retrieving the current emote from the game's emote list
    2. Fetching the emote's URL from the database
    3. Generating a description for the emote using image recognition
    4. Sending the emote description to the channel
    5. Starting timers for round duration and hint provision
    
    Parameters:
        channel (str): The IRC channel where the game is being played
    
    Behavior:
        - Handles cases where emote URL is missing or description generation fails
        - Automatically advances to the next round or ends the game if issues occur
        - Starts a 40-second round timer
        - Triggers a hint after 20 seconds
        - Sends descriptive messages to guide players
    
    Raises:
        Handles potential exceptions during image processing and description generation
    """
    currentEmote = self.gameEmotes[self.currentRound]
    emote_url = self.db['Emotes'].find_one({"name": currentEmote})["url"]
    
    if not emote_url:
        self.send_privmsg(
            channel, "Emote was not found in database! Moving on to next round...")
        time.sleep(0.5)
        if self.guessGameRoundTimer:
            self.guessGameRoundTimer.cancel()
        if self.hintTimer:
            self.hintTimer.cancel()
        if is_game_over(self.currentRound, self.numRounds):
            # end the game
            self.send_privmsg(channel, "Game has ended.")
            reset_game(self)
            return
        self.currentRound += 1
        start_new_round(self, channel)
        return

    descr = "Give a description for this emote in 2 sentences. Start with 'This emote'"
    try:
        if describe.is_chunked(emote_url):
            image_content = requests.get(emote_url, stream=True).content
            image = Image.open(io.BytesIO(image_content)).convert("RGB")
        else:
            image = Image.open(requests.get(emote_url, stream=True).raw)
        description = gemini.generate_emote_description([image, descr])
    except Exception as e:
        print(e)
        self.send_privmsg(channel, str(e)[0:400])
        time.sleep(0.5)
        self.send_privmsg(
            channel, "Emote was not found in database! Moving on to next round...")
        time.sleep(0.5)
        if self.guessGameRoundTimer:
            self.guessGameRoundTimer.cancel()
        if self.hintTimer:
            self.hintTimer.cancel()
        if is_game_over(self.currentRound, self.numRounds):
            # end the game
            self.send_privmsg(channel, "Game has ended.")
            reset_game(self)
            return
        self.currentRound += 1
        start_new_round(self, channel)
        return

    if not description:
        self.send_privmsg(
            channel, "Emote description could not be generated. Moving on to next round...")
        time.sleep(0.5)
        if self.guessGameRoundTimer:
            self.guessGameRoundTimer.cancel()
        if self.hintTimer:
            self.hintTimer.cancel()
        if is_game_over(self.currentRound, self.numRounds):
            # end the game
            self.send_privmsg(channel, "Game has ended.")
            reset_game(self)
            return
        self.currentRound += 1
        start_new_round(self, channel)
        return

    self.send_privmsg(
        channel, f"Round {self.currentRound + 1}: {description} Guess the emote!")  # Display round as 1-based

    # Start the 40-second timer for this round
    self.guessGameRoundTimer = Timer(
        40, reveal_emote, (self, channel, currentEmote))
    self.guessGameRoundTimer.start()

    # Start the hint timer after 20 seconds
    self.hintTimer = Timer(
        20, provide_hint, (self, channel, emote_url))
    self.hintTimer.start()

def reward(self, message):
    # reward 25 coins for correct answer
    user_data = self.users.find_one({'user': message['source']['nick']})
    if not user_data: # add new user
        self.users.insert_one({'user': message['source']['nick'] , 'points': 0 })
    self.users.update_one({'user': message['source']['nick']}, {'$inc': {'points': 25}})

def provide_hint(self, channel, emote_url):
    # Provide a hint from ascii
    hint = ascii.first_frame(channel, emote_url)
    self.send_privmsg(channel, hint)

def is_game_over(current_round, num_rounds):
    return current_round + 1 == num_rounds

def reveal_emote(self, channel, emote):
    self.send_privmsg(
        channel, f"The emote was {emote} Disappointing performance :Z")

    if is_game_over(self.currentRound, self.numRounds):
        # End the game if all rounds are done
        self.send_privmsg(channel, "Game has ended.")
        reset_game(self)
    else:
        # Start the next round
        self.currentRound += 1
        time.sleep(1.1)
        start_new_round(self, channel)


def get_current_emote(self):
    if self.guessGameActive and self.gameEmotes:
        return self.gameEmotes[self.currentRound]


def reset_game(self):
    self.guessGameActive = False
    self.currentRound = 0
    self.gameEmotes = []
    self.numRounds = 5
    self.guessGameRoundTimer = None
    self.hintTimer = None
    return


def get_random_emotes(self, channel_id, num_emotes=5, is_global=False):
    if is_global:
        # Fetch global Twitch emotes
        global_emote_records = self.db['Emotes'].find({"emote_type": "Twitch"})
        global_emotes = [emote['name'] for emote in global_emote_records]

        # If fewer emotes found, return all available
        if len(global_emotes) <= num_emotes:
            return global_emotes

        # Return a random sample of global emotes
        return random.sample(global_emotes, num_emotes)

    # Fetch emote IDs from the ChannelEmotes collection
    emote_records = self.db['ChannelEmotes'].find(
        {"channel_id": channel_id}, {"emote_id": 1})
    emote_ids = [record['emote_id'] for record in emote_records]

    if not emote_ids:
        return []

    # Select random emote_ids (limit the number of emotes if needed)
    random_emote_ids = random.sample(
        emote_ids, min(num_emotes, len(emote_ids)))

    # Fetch emote names using the $in operator in one query
    emote_records = self.db['Emotes'].find(
        {"emote_id": {"$in": random_emote_ids}}, {"name": 1})

    # Collect the names from the query result
    emote_names = [emote['name'] for emote in emote_records]

    # If no names found, return an empty list
    if not emote_names:
        return []

    return emote_names
