# BluePagmanBot
A Twitch chatbot running in Python. 

##  Major Features:
- Get a random chess opening name, can add specific keywords, and/or indicate the side.
- Play a chess game through sending messages, with a dynamically updated PGN of the ongoing game.
- Get a random news headline from Google News.
- Gambling with points.

## Prerequisites: 
[Python 3.7+](https://www.python.org/downloads/)

[python-chess](https://pypi.org/project/chess/)

[feedparser](https://pypi.org/project/feedparser/)

For versions 1.3 and higher:
[pymongo](https://pypi.org/project/pymongo/)

## How to use: 

IMPORTANT: If you don't want to set up a MongoDB, then use v1.2 in releases.

1. Download the latest release and extract.
2. Make a Twitch account if you do not already have one.
3. Get the OAuth token of the Twitch account to be used as the bot [here](https://twitchapps.com/tmi/).
4. Rename `config_example.py` to `config.py`, and fill in the details.
5. Set up a Mongo database, add a database named "test" and a collection named "Users". Then add the connection string into `config.py` in db_uri.
6. Run `bot.py`. The bot will now join the channels you put in `config.py`.

## Screenshots: 

<img src="https://user-images.githubusercontent.com/82780692/187820763-d8b24c7f-979a-42ca-b28e-d872e84f0c0e.png"> <img  src="https://user-images.githubusercontent.com/82780692/187818815-f37aa7df-b9ed-4d67-b32c-f58cc55ea2ba.png">
