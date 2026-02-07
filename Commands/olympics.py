import random, requests, time, pycountry
from Utils.utils import check_cooldown, fetch_cmd_data, proxy_request


def reply_with_olympics(self, message):
    cmd = fetch_cmd_data(self, message)
    if not check_cooldown(cmd.state, cmd.nick, cmd.cooldown): 
        return
    
    link = "https://www.olympics.com/wmr-owg2026/competition/api/ENG/medals"

    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "en,en-US;q=0.9",
        "cache-control": "max-age=0",
        "priority": "u=0, i",
        "sec-ch-ua": '"Not(A:Brand";v="8", "Chromium";v="144", "Google Chrome";v="144"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "Windows",
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "none",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36"
    }

    try:
        response = proxy_request("GET", link, headers=headers)
        data = response.json()
    except (requests.RequestException, ValueError) as exc:
        self.send_privmsg(cmd.channel, f"Could not fetch medal data: {exc}")
        return
    
    medals_table = data.get("medalStandings", {}).get("medalsTable", [])
    
    if not medals_table:
        self.send_privmsg(cmd.channel, "No medal data available yet.")
        return

    if cmd.params:
        param = cmd.params.upper()
        
        if param == "TOP":
            top5 = medals_table[:5]
            lines = []
            for i, country in enumerate(top5, 1):
                c_name = country.get("description", "Unknown")
                flag = get_flag_from_name(c_name)
                
                # Get total medals
                medals_numbers = country.get("medalsNumber", [])
                total_medals_data = next((m for m in medals_numbers if m.get("type") == "Total"), {})
                g = total_medals_data.get("gold", 0)
                s = total_medals_data.get("silver", 0)
                b = total_medals_data.get("bronze", 0)
                t = total_medals_data.get("total", 0)
                
                lines.append(f"{i}. {flag} {c_name}: {g}G {s}S {b}B ({t})")
            
            self.send_privmsg(cmd.channel, " | ".join(lines))
            return
        
        country_data = None
        for country in medals_table:
            c_name = country.get("description", "").upper()
            c_noc = country.get("organisation", "").upper()
            
            if c_noc == param or c_name == param:
                country_data = country
                break
        
        if not country_data:
            self.send_privmsg(cmd.channel, "The country has no medals.")
            return
        
        text = format_country_medals(country_data)
        self.send_privmsg(cmd.channel, text)
        return
    
    # No params - get random country
    country = medals_table[random.randint(0, len(medals_table) - 1)]
    text = format_country_medals(country)
    self.send_privmsg(cmd.channel, text)


def format_country_medals(country_data):
    # Format medal data for a country into a readable string.
    country_name = country_data.get("description", "Unknown")
    rank = country_data.get("rank", "N/A")
    
    medals_numbers = country_data.get("medalsNumber", [])
    total_medals = None
    for medal_type in medals_numbers:
        if medal_type.get("type") == "Total":
            total_medals = medal_type
            break
    
    if total_medals:
        golds = total_medals.get("gold", 0)
        silvers = total_medals.get("silver", 0)
        bronzes = total_medals.get("bronze", 0)
        total = total_medals.get("total", 0)
    else:
        golds = silvers = bronzes = total = 0
    
    flag = get_flag_from_name(country_name)
    
    return f"{flag} {country_name} has {golds} gold, {silvers} silver, and {bronzes} bronze medals, for a total of {total}. Their overall rank is {rank}."


def get_flag_from_name(name):
    # Get the flag emoji for a country name using pycountry
    try:
        matches = pycountry.countries.search_fuzzy(name)
        if matches:
            return country_code_to_flag(matches[0].alpha_2)
    except (LookupError, AttributeError):
        pass
    return ""


def country_code_to_flag(country_code):
    country_code = country_code.upper()
    flag = ''.join(chr(0x1F1E6 + ord(char) - ord('A')) for char in country_code)
    return flag