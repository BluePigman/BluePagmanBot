from Utils.utils import check_cooldown, fetch_cmd_data
import requests, re
from datetime import datetime

APP_ID = "79frdp12pn"
RESULTS_MAX = 50
SEARCH_PARAMS = {
    "x-algolia-api-key": "175588f6e5f8319b27702e4cc4013561",
    "x-algolia-application-id": APP_ID.upper()
}


def _search_rt(query):
    try:
        r = requests.post(
            f"https://{APP_ID}-1.algolianet.com/1/indexes/*/queries",
            params=SEARCH_PARAMS,
            json={"requests": [{"indexName": "content_rt", "params": f"hitsPerPage={RESULTS_MAX}&query={query}"}]},
            timeout=5
        )
        return r.json()['results'][0]['hits'] if r.ok else None
    except requests.RequestException:
        return None


def _format(t):
    rt = t.get('rottenTomatoes', {})
    aud = rt.get('audienceScore', 'N/A')
    crt = rt.get('criticsScore', 'N/A')
    aud = f"{aud}%" if str(aud).isnumeric() else aud
    crt = f"{crt}%" if str(crt).isnumeric() else crt
    icon = rt.get('criticsIconUrl')
    rating = "🍅" if rt.get('certifiedFresh') else "🗑️" if icon and "rotten" in icon else "ok "
    tp = t.get('type') or 'N/A'
    tp_str = tp.capitalize()
    path = "m" if tp == "movie" else "tv"
    cast_crew = t.get('castCrew') or {}
    crew = cast_crew.get('crew') or {}
    director = ", ".join(crew.get('Director', [])) or "N/A"
    cast = ", ".join((cast_crew.get('cast') or [])[:4]) or "N/A"
    genres = ", ".join(t.get('genres', [])[:4]) or "N/A"
    runtime = f"{t['runTime']} min" if t.get('runTime') else "N/A"
    url = f"https://www.rottentomatoes.com/{path}/{t.get('vanity') or ''}"
    return (f"Rotten Tomatoes scores for {tp_str} {t.get('title', 'N/A')} ({t.get('releaseYear', 'N/A')}) "
            f"- Rating: {rating}, Audience: {aud}, Critics: {crt}, 🎬 Director: {director}, "
            f"👥 Cast: {cast}, 🏷️ Genres: {genres}, ⏱️ Runtime: {runtime}, {url}")


def rottentomatoes(query, year=None):
    if not query:
        return "No query provided!"

    if year is not None:
        if year > datetime.now().year:
            return "Invalid year provided!"
        results = _search_rt(query)
        if not results:
            return "No results found."
        return _format(sorted(results, key=lambda x: abs(year - int(x.get('releaseYear') or 0)))[0])

    # Find 4-digit number in query
    match = re.search(r'\b(\d{4})\b', query)
    if not match:
        results = _search_rt(query)
        if not results:
            return "No results found."
        return _format(results[0])

    num = int(match.group(1))
    results = _search_rt(query)

    # If the number is in a top result's title, use that result
    for hit in (results or [])[:5]:
        if str(num) in hit.get('title', ''):
            return _format(hit)

    # Otherwise treat the number as a year filter
    if num > datetime.now().year:
        return "Invalid year provided!"
    stripped = re.sub(r'\s+', ' ', query.replace(match.group(1), '')).strip()
    results = _search_rt(stripped)
    if not results:
        return "No results found."
    return _format(sorted(results, key=lambda x: abs(num - int(x.get('releaseYear') or 0)))[0])


def reply_with_rottentomatoes(self, message):
    cmd = fetch_cmd_data(self, message)
    if not check_cooldown(cmd.state, cmd.nick, cmd.cooldown):
        return
    if not cmd.params:
        self.send_privmsg(cmd.channel, f"{cmd.username}, please provide a movie/show name")
        return

    query = cmd.params
    year = None
    if 'year:' in query:
        for part in query.split():
            if part.startswith('year:'):
                try:
                    year = int(part.split(':')[1])
                    query = query.replace(part, '').strip()
                except ValueError:
                    self.send_privmsg(cmd.channel, f"{cmd.username}, invalid year format. Use 'year:XXXX'.")
                    return

    self.send_privmsg(cmd.channel, rottentomatoes(query, year))