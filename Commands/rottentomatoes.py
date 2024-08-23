import time
import requests
from datetime import datetime

APP_ID = "79frdp12pn"
RESULTS_MAX = 50
BASE_SEARCH_PARAMS = {
    "x-algolia-api-key": "175588f6e5f8319b27702e4cc4013561",
    "x-algolia-application-id": APP_ID.upper()
}

def rottentomatoes(query, year=None):
    if not query:
        return "No query provided!"

    current_year = datetime.now().year
    if year and year > current_year:
        return "Invalid year provided!"

    response = requests.post(
        f"https://{APP_ID}-1.algolianet.com/1/indexes/*/queries",
        params=BASE_SEARCH_PARAMS,
        json={
            "requests": [{
                "indexName": "content_rt",
                "params": f"hitsPerPage={RESULTS_MAX}&query={query}"
            }]
        }
    )

    if not response.ok:
        return "Could not fetch data from RottenTomatoes! Try again later."

    results = response.json()['results'][0]['hits']
    if not results:
        return "No results found for the query provided!"
    
    sorted_results = sorted(
        results,
        key=lambda x: abs(year - x.get('releaseYear', 0)) if year else -x.get('pageViews_popularity', 0)
    )

    target = sorted_results[0]
    title = target['title']
    release_year = target['releaseYear']
    type_ = target['type']
    vanity = target['vanity']
    rotten_tomatoes = target.get('rottenTomatoes', {})
    certified_fresh = rotten_tomatoes.get('certifiedFresh')
    audience_score = rotten_tomatoes.get('audienceScore', "N/A")
    audience_score = f"{audience_score}%" if str(audience_score).isnumeric() else audience_score
    critics_score = rotten_tomatoes.get('criticsScore', "N/A")
    critics_score = f"{critics_score}%" if str(critics_score).isnumeric() else critics_score
    critics_icon_url = rotten_tomatoes.get('criticsIconUrl')
    path = "m" if type_ == "movie" else "tv"
    url = f"https://www.rottentomatoes.com/{path}/{vanity}"

    rating = "🍅" if certified_fresh else "🗑️" if critics_icon_url and "rotten" in critics_icon_url else "mid "

    return f"Rotten Tomatoes scores for {type_.capitalize()} {title} ({release_year}) - Rating: {rating}, \
          Audience: {audience_score}, Critics: {critics_score}, {url}"


def reply_with_rottentomatoes(self, message):
    if (message['source']['nick'] not in self.state or time.time() - self.state[message['source']['nick']] > self.cooldown):
        self.state[message['source']['nick']] = time.time()

    if not message['command']['botCommandParams']:
        m = f"@{message['tags']['display-name']}, please provide a movie/show name, optionally add year with year:XXXX"
        self.send_privmsg(message['command']['channel'], m)
        return

    query = message['command']['botCommandParams']
    
    # Extract year if provided in the format 'year:XXXX'
    year = None
    if 'year:' in query:
        parts = query.split()
        for part in parts:
            if part.startswith('year:'):
                try:
                    year = int(part.split(':')[1])
                    query = query.replace(part, '').strip()  # Remove the year part from the query
                except ValueError:
                    m = f"@{message['tags']['display-name']}, invalid year format. Please use 'year:XXXX'."
                    self.send_privmsg(message['command']['channel'], m)
                    return

    result = rottentomatoes(query, year)
    self.send_privmsg(message['command']['channel'], result)
