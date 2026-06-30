from datetime import datetime
from zoneinfo import ZoneInfo
import requests
import pycountry
from Utils.utils import check_cooldown, fetch_cmd_data, send_chunks


def reply_with_football_scores(self, message):
    cmd = fetch_cmd_data(self, message)
    if not check_cooldown(cmd.state, cmd.nick, cmd.cooldown): 
        return

    football_scores = get_football_scores()
    send_chunks(self.send_privmsg, cmd.channel, football_scores)


def country_code_to_flag(country_code):
    country_code = country_code.upper()
    return ''.join(chr(0x1F1E6 + ord(char) - ord('A')) for char in country_code)


def get_flag(team):
    abbr = team.get('abbreviation')
    if abbr:
        try:
            country = pycountry.countries.get(alpha_3=abbr.upper())
            if country:
                return country_code_to_flag(country.alpha_2)
        except Exception:
            pass
            
    name = team.get('displayName') or team.get('name')
    if name:
        try:
            matches = pycountry.countries.search_fuzzy(name)
            if matches:
                return country_code_to_flag(matches[0].alpha_2)
        except Exception:
            pass
            
    return ""


def get_football_scores():
    url = "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard"
    try:
        response = requests.get(url)
        data = response.json()
        
        eastern = ZoneInfo('America/New_York')
        now = datetime.now(eastern)
        
        results = []
        
        if not data.get('events'):
            return "No FIFA World Cup games are scheduled for today."
            
        for event in data['events']:
            game_status = event['status']['type']['state']
            competition = event['competitions'][0]
            
            home_competitor = competition['competitors'][0] if competition['competitors'][0]['homeAway'] == 'home' else competition['competitors'][1]
            away_competitor = competition['competitors'][1] if competition['competitors'][0]['homeAway'] == 'home' else competition['competitors'][0]
            
            home_team = home_competitor['team']
            away_team = away_competitor['team']
            
            home_flag = get_flag(home_team)
            away_flag = get_flag(away_team)
            
            home_name = home_team.get('displayName', home_team.get('name', 'Unknown'))
            away_name = away_team.get('displayName', away_team.get('name', 'Unknown'))
            
            home_display = f"{home_flag} {home_name}".strip() if home_flag else home_name
            away_display = f"{away_flag} {away_name}".strip() if away_flag else away_name
            
            home_score = home_competitor.get('score', '0')
            away_score = away_competitor.get('score', '0')
            
            game_text = ""
            
            if game_status == 'pre':
                game_date = event['date']
                game_time = datetime.strptime(game_date, "%Y-%m-%dT%H:%MZ")
                game_time = game_time.replace(tzinfo=ZoneInfo('UTC')).astimezone(eastern)
                est_time = game_time.strftime("%I:%M %p EST")
                
                time_diff = game_time - now
                hours, remainder = divmod(time_diff.total_seconds(), 3600)
                minutes = remainder // 60
                
                if time_diff.total_seconds() < 0:
                    game_text = f"{away_display} vs {home_display} (Starting soon)"
                else:
                    if hours > 0:
                        if minutes > 0:
                            time_until = f"in {int(hours)}h {int(minutes)}m"
                        else:
                            time_until = f"in {int(hours)}h"
                    else:
                        time_until = f"in {int(minutes)}m"
                    game_text = f"{away_display} vs {home_display} ({est_time}, {time_until})"
                    
            elif game_status == 'in':
                status_detail = competition['status']['type'].get('detail', '')
                status_desc = competition['status']['type'].get('description', '')
                
                status = status_detail if status_detail else status_desc
                
                home_shootout = home_competitor.get('shootoutScore')
                away_shootout = away_competitor.get('shootoutScore')
                
                if home_shootout is not None and away_shootout is not None:
                    game_text = f"{away_display} {away_score} - {home_score} {home_display} ({status}, {away_shootout}-{home_shootout} Pens)"
                else:
                    game_text = f"{away_display} {away_score} - {home_score} {home_display} ({status})"
                
            elif game_status == 'post':
                status_detail = competition['status']['type'].get('detail', 'FT')
                
                home_shootout = home_competitor.get('shootoutScore')
                away_shootout = away_competitor.get('shootoutScore')
                
                if status_detail == 'FT':
                    status_display = 'FINAL'
                elif status_detail == 'FT-Pens' or 'Pens' in status_detail or (home_shootout is not None and away_shootout is not None):
                    if home_shootout is not None and away_shootout is not None:
                        home_won = home_competitor.get('winner') is True
                        away_won = away_competitor.get('winner') is True
                        if home_won:
                            winner_name = home_name
                        elif away_won:
                            winner_name = away_name
                        else:
                            try:
                                home_sh = int(home_shootout)
                                away_sh = int(away_shootout)
                                winner_name = home_name if home_sh > away_sh else away_name
                            except (ValueError, TypeError):
                                winner_name = home_name if home_competitor.get('winner') is True or (home_competitor.get('advance') is True) else away_name
                        
                        try:
                            home_sh = int(home_shootout)
                            away_sh = int(away_shootout)
                            high_score = max(home_sh, away_sh)
                            low_score = min(home_sh, away_sh)
                        except (ValueError, TypeError):
                            high_score = home_shootout
                            low_score = away_shootout
                            
                        status_display = f'FINAL ({status_detail}, {winner_name} wins {high_score}-{low_score})'
                    else:
                        status_display = f'FINAL ({status_detail})'
                else:
                    status_display = f'FINAL ({status_detail})'
                    
                game_text = f"{away_display} {away_score} - {home_score} {home_display} {status_display}"
                
            results.append(game_text)
            
        return " | ".join(results)
    except Exception as e:
        print(f"Error fetching World Cup scores: {e}")
        return "Could not fetch World Cup scores. Try again later."