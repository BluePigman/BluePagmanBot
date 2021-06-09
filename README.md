# BluePagmanBot
A Twitch chatbot running in Python. 

## Prerequisites: 
[Python 3+](https://www.python.org/downloads/)

[python-chess](https://pypi.org/project/chess/)
## NOTE: PLEASE ADD Chess 960 FENS.txt to the bot directory, or else the r960 command will not work.
## How to install: 

1. Download the latest release and extract into a folder. Make sure all files are in the same folder.
2. Make a Twitch account if you do not already have one.
3. Get the OAuth token of the account to be used as the bot [here](https://twitchapps.com/tmi/).
4. Put the OAuth token in the config file, and edit the rest of the config file.
5. Run the bot.py file, and now the bot is running. If set up properly, the bot will send message "forsenEnter". (This can be changed later)
6. You can add commands by adding a function and putting it in the dictionary (copy the other commands format).
