from datetime import datetime
from zoneinfo import ZoneInfo
import requests
from Utils.utils import check_cooldown, fetch_cmd_data


def reply_with_nba_scores(self, message):
    cmd = fetch_cmd_data(self, message)
    if not check_cooldown(cmd.state, cmd.nick, cmd.cooldown): 
        return

    nba_scores = get_nba_scores()
    self.send_privmsg(cmd.channel, nba_scores)


def get_nba_scores():
    url = "http://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        eastern = ZoneInfo('America/New_York')
        now = datetime.now(eastern)
        
        results = []
        
        if not data.get('events'):
            return "No NBA games are scheduled for today."
        
        for event in data['events']:
            game_status = event['status']['type']['state']
            competition = event['competitions'][0]
            
            home_team = competition['competitors'][0] if competition['competitors'][0]['homeAway'] == 'home' else competition['competitors'][1]
            away_team = competition['competitors'][1] if competition['competitors'][0]['homeAway'] == 'home' else competition['competitors'][0]
            
            home_team_name = f"{home_team['team']['location']} {home_team['team']['name']}"
            away_team_name = f"{away_team['team']['location']} {away_team['team']['name']}"
            
            home_score = home_team['score']
            away_score = away_team['score']
            
            game_text = ""
            
            if game_status == 'pre':  # Game hasn't started
                game_date = event['date']
                game_time = datetime.strptime(game_date, "%Y-%m-%dT%H:%MZ")
                game_time = game_time.replace(tzinfo=ZoneInfo('UTC')).astimezone(eastern)
                est_time = game_time.strftime("%I:%M %p EST")
                
                # Calculate time until game starts
                time_diff = game_time - now
                hours, remainder = divmod(time_diff.total_seconds(), 3600)
                minutes = remainder // 60
                
                # Handle negative time (if API hasn't updated status yet)
                if time_diff.total_seconds() < 0:
                    game_text = f"{away_team_name} vs {home_team_name} (Starting soon)"
                else:
                    if hours > 0:
                        time_until = f"{int(hours)}h {int(minutes)}m from now"
                    else:
                        time_until = f"{int(minutes)}m from now"
                        
                    game_text = f"{away_team_name} vs {home_team_name} ({est_time}, {time_until})"
                
            elif game_status == 'in':  # Game in progress
                period = competition['status']['period']
                clock = competition['status']['displayClock']
                
                # Determine period display (regular quarter or overtime)
                if period <= 4:
                    period_display = f"Q{period}"
                else:
                    ot_number = period - 4
                    period_display = f"OT{ot_number}"
                
                if clock == '0:00':
                    if period == 1:
                        status = "End of Q1"
                    elif period == 2:
                        status = "Halftime"
                    elif period == 3:
                        status = "End of Q3"
                    elif period == 4:
                        status = "End of Q4"
                    else:
                        status = f"End of OT{period-4}"
                else:
                    status = f"{period_display} {clock} remaining"
                    
                game_text = f"{away_team_name} {away_score} - {home_score} {home_team_name} {status}"
                
            elif game_status == 'post':  # Game completed
                # Check if game went to overtime
                period = competition['status'].get('period', 4)
                if period > 4:
                    ot_number = period - 4
                    ot_display = f" (OT{ot_number})"
                else:
                    ot_display = ""
                    
                game_text = f"{away_team_name} {away_score} - {home_score} {home_team_name} FINAL{ot_display}"
            
            results.append(game_text)
        
        return " | ".join(results)
    
    except Exception as e:
        return f"Error fetching NBA scores: {str(e)}"