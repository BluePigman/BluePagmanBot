import random
import requests, time
from Utils.utils import check_cooldown, fetch_cmd_data


def reply_with_olympics(self, message):
    cmd = fetch_cmd_data(self, message)
    if not check_cooldown(cmd.state, cmd.nick, cmd.cooldown): 
        return
    
    link = "https://bluepigman.github.io/2024-olympics/medals.json"
    if cmd.params:
        countryCode = cmd.params.split()[0]
        if len(countryCode) != 3:
            self.send_privmsg(cmd.channel, "Please enter a valid NOC code for the country: https://en.wikipedia.org/wiki/List_of_IOC_country_codes#Current_NOCs")
            return
        if countryCode.lower() != "top":
            link += f"?country={countryCode}"

    try:
        response = requests.get(link, timeout=5)
        response = response.json()
    except (requests.RequestException, ValueError) as exc:
        self.send_privmsg(cmd.channel, f"Could not fetch medal data: {exc}")
        return
    
    if not response["results"]:
        self.send_privmsg(cmd.channel, "The country has no medals or the code does not exist.")
        return
    if response["length"] == 1: # individual country
        medals = response["results"][0]["medals"]
        golds = medals["gold"]
        silvers = medals["silver"]
        bronzes = medals["bronze"]
        total = medals["total"]
        flag = country_code_to_flag(response["results"][0]["country"]["iso_alpha_2"])
        
        rank = response["results"][0]["rank"]
        country = response["results"][0]["country"]["name"]

        text = f"{flag} {country} has {golds} gold, {silvers} silver, and {bronzes} bronze medals, for a total of {total}. Their overall rank is {rank}."

        self.send_privmsg(cmd.channel, text)
        return
    
    if not cmd.params:
        # get random country
        country = response["results"][random.randint(0, response["length"]-1)]
        countryName = country["country"]["name"]
        medals = country["medals"]
        golds = medals["gold"]
        silvers = medals["silver"]
        bronzes = medals["bronze"]
        total = medals["total"]
        flag = country_code_to_flag(country["country"]["iso_alpha_2"])
        
        text = f"{flag} {countryName} has {golds} gold, {silvers} silver, and {bronzes} bronze medals, for a total of {total}."
        self.send_privmsg(cmd.channel, text)
        return
    
    # overall, get top 5   
    if cmd.params.split()[0] == "top":
        top5 = response["results"][:5]
        for country in top5:
            rank = country["rank"]
            countryName = country["country"]["name"]
            medals = country["medals"]
            golds = medals["gold"]
            silvers = medals["silver"]
            bronzes = medals["bronze"]
            total = medals["total"]
            flag = country_code_to_flag(country["country"]["iso_alpha_2"])
            
            text = f"{flag} {countryName} has {golds} gold, {silvers} silver, and {bronzes} bronze medals, for a total of {total}. Their overall rank is {rank}."
            self.send_privmsg(cmd.channel, text)
            time.sleep(1)



def country_code_to_flag(country_code):
    country_code = country_code.upper()
    # Calculate the Unicode code points for the regional indicator symbols
    flag = ''.join(chr(0x1F1E6 + ord(char) - ord('A')) for char in country_code)
    return flag
