# BluePagmanBot
A Twitch chatbot running in Python. 

##  Major Features:
- Interact with Google Gemini to ask it questions, generate images, describe image and video links, and summarize Youtube videos.
- Generate Braille/ASCII art from emotes/image links.
- Get a random news headline from Google News.
- Play various games: Gambling with points, Guess the Emote
- Show lyrics of a song from Genius.
- Fetch a random post or comment from a subreddit on Reddit.
- Play a chess game through sending messages, with a dynamically updated PGN of the ongoing game.
- Get a random chess opening name, can add specific keywords, and/or indicate the side.


## Prerequisites
- [Python 3.9+](https://www.python.org/downloads/)
- MongoDB Server ([Atlas](https://www.mongodb.com/products/platform/atlas-database) is the easiest to set up)
- Twitch Account

## How to use: 

1. Fork or clone this repository.
2. Create a [python virtual environment](https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/#create-and-use-virtual-environments) and run `pip install -e .` in the project's directory. (The `-e` flag installs the package in editable mode, which is useful for development.)
3. Get an OAuth token of the Twitch account for the bot. I used [this](https://twitchapps.com/tmi/) to generate one, but the site has now shut down, so please find another way to get one. You can get the access token and Client ID [here](http://twitchtokengenerator.com/)
5. Rename `config_example.py` to `config.py`, and fill in the details.
6. Set up a Mongo database, add a database named "test" and a collection named "Users". Then add the connection string into `config.py` in db_uri.
7. Run `bot.py`. The bot will now join the channels you put in `config.py`.

## Maintenance:
`uv add` to add packages. Then `pip install -e .` to update.

## Video Demo:
https://github.com/BluePigman/BluePagmanBot/assets/82780692/6cab58f2-3a63-4344-9456-abce8bc93851

## Screenshots: 

<img src="https://user-images.githubusercontent.com/82780692/187820763-d8b24c7f-979a-42ca-b28e-d872e84f0c0e.png"> <img  src="https://user-images.githubusercontent.com/82780692/187818815-f37aa7df-b9ed-4d67-b32c-f58cc55ea2ba.png">


## Credits:

This bot takes a lot of functionality from https://github.com/VJ-Duardo/VJBotardo


https://github.com/VJ-Duardo/PyBrailleArt for Braille Art

https://github.com/SSujitX/google-news-url-decoder to decode Google News URLs

And everyone else that helped me with testing by using the bot, thank you!
