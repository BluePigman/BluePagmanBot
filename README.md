# BluePagmanBot
A Twitch chatbot running in Python. 

##  Major Features:
- Generate text from a text prompt using Google Gemini.
- Get a random chess opening name, can add specific keywords, and/or indicate the side.
- Play a chess game through sending messages, with a dynamically updated PGN of the ongoing game.
- Get a random news headline from Google News.
- Gambling with points.
- Generates Braille/ASCII art from emotes/image links.
- Play Texas Hold'em poker with multiple people.
- Summarize Youtube videos (sends transcript to Gemini).
- Describe image and video links (uploads to Gemini and asks for description).
## Prerequisites: 
[Python 3.8+](https://www.python.org/downloads/)

[chess](https://pypi.org/project/chess/)

[feedparser](https://pypi.org/project/feedparser/)

[requests](https://pypi.org/project/requests/)

For versions 1.3 and higher:
[pymongo](https://pypi.org/project/pymongo/)

``pip install --upgrade google-cloud-aiplatform``


``gcloud auth application-default login``

``pip install texasholdem``

``pip install beautifulsoup4``

``pip install youtube_transcript_api``

``pip install -U google-generativeai``

``pip install selectolax``


## How to use: 

IMPORTANT: If you don't want to set up a MongoDB, then use v1.2 in releases.

1. Download the latest release and extract.
2. Make a Twitch account if you do not already have one.
3. Get the OAuth token of the Twitch account to be used as the bot [here](https://twitchapps.com/tmi/).
4. Rename `config_example.py` to `config.py`, and fill in the details.
5. Set up a Mongo database, add a database named "test" and a collection named "Users". Then add the connection string into `config.py` in db_uri.
6. Run `bot.py`. The bot will now join the channels you put in `config.py`.

## Video Demo:
https://github.com/BluePigman/BluePagmanBot/assets/82780692/6cab58f2-3a63-4344-9456-abce8bc93851

## Screenshots: 

<img src="https://user-images.githubusercontent.com/82780692/187820763-d8b24c7f-979a-42ca-b28e-d872e84f0c0e.png"> <img  src="https://user-images.githubusercontent.com/82780692/187818815-f37aa7df-b9ed-4d67-b32c-f58cc55ea2ba.png">


## Credits:

This bot takes a lot of functionality from https://github.com/VJ-Duardo/VJBotardo


https://github.com/VJ-Duardo/PyBrailleArt for Braille Art
https://github.com/kevle1/paris-2024-olympic-api for getting 2024 Olympics medal counts
https://github.com/SSujitX/google-news-url-decoder to decode Google News URLs

And everyone else that helped me with testing by using the bot, thank you!
