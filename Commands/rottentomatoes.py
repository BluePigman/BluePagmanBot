from Utils.utils import (
    check_cooldown,
    fetch_cmd_data,
    proxy_request,
    log_err
)
import re, datetime
from urllib.parse import quote

APP_ID = "79frdp12pn"
RT_SEARCH_URL = f"https://{APP_ID}-1.algolianet.com/1/indexes/*/queries"

RESULTS_MAX = 50
SEARCH_PARAMS = {
    "x-algolia-api-key": "175588f6e5f8319b27702e4cc4013561",
    "x-algolia-application-id": APP_ID.upper()
}


def _search_rt(query, year=None):
    try:
        current_year = datetime.datetime.now().year

        if year is not None and not (1888 <= year <= current_year + 15):
            year = None

        payload = {
            "requests": [
                {
                    "indexName": "content_rt",
                    "params": f"hitsPerPage={RESULTS_MAX}&query={quote(query)}"
                }
            ]
        }

        response = proxy_request(
            "POST",
            RT_SEARCH_URL,
            params=SEARCH_PARAMS,
            json=payload,
            timeout=5
        )

        if not response.ok:
            return None

        data = response.json()
        results = data.get("results")

        if not results:
            return None

        hits = results[0].get("hits") or []

        if year is not None:
            sorted_hits = sorted(
                hits,
                key=lambda x: abs(year - int(x.get("releaseYear") or 0))
            )
            return sorted_hits

        return hits

    except Exception:
        return None


def _format(t):
    rt = t.get('rottenTomatoes', {})
    aud = rt.get('audienceScore', 'N/A')
    crt = rt.get('criticsScore', 'N/A')

    aud = f"{aud}%" if str(aud).isnumeric() else aud
    crt = f"{crt}%" if str(crt).isnumeric() else crt

    icon = rt.get('criticsIconUrl')
    rating = "🍅" if rt.get('certifiedFresh') else "🗑️" if icon and "rotten" in icon else "ok "

    media_type = t.get('type') or 'N/A'
    type_str = media_type.capitalize()
    path = "m" if media_type == "movie" else "tv"

    cast_crew = t.get('castCrew') or {}
    crew = cast_crew.get('crew') or {}

    director = ", ".join(crew.get('Director', [])) or "N/A"
    cast = ", ".join((cast_crew.get('cast') or [])[:4]) or "N/A"
    genres = ", ".join(t.get('genres', [])[:4]) or "N/A"
    runtime = f"{t['runTime']} min" if t.get('runTime') else "N/A"

    url = f"https://www.rottentomatoes.com/{path}/{t.get('vanity') or ''}"

    return (
        f"Rotten Tomatoes scores for {type_str} {t.get('title', 'N/A')} ({t.get('releaseYear', 'N/A')}) "
        f"- Rating: {rating}, Audience: {aud}, Critics: {crt}, 🎬 Director: {director}, "
        f"👥 Cast: {cast}, 🏷️ Genres: {genres}, ⏱️ Runtime: {runtime}, {url}"
    )


def extract_year(query):
    # matches trailing year formats like:
    # "Inception 2010"
    # "Inception (2010)"
    # "Inception [2010]"
    match = re.search(r'[\(\[]?(\d{4})[\)\]]?$', query)

    if not match:
        return {
            "cleaned_query": query,
            "year": None
        }

    return {
        "cleaned_query": query[:match.start()].strip(),
        "year": int(match.group(1))
    }


def reply_with_rottentomatoes(self, message):
    try:
        cmd = fetch_cmd_data(self, message, arg_types={"year": int}, split_params=True)

        if not check_cooldown(cmd.state, cmd.nick, cmd.cooldown):
            return

        if not cmd.params:
            self.send_privmsg(cmd.channel, f"{cmd.username}, please provide a movie/show name")
            return

        query = " ".join(cmd.params)
        year = cmd.args.get("year")

        # only search query for the year when -year is not passed and query longer than one word
        if year is None and len(cmd.params) > 1:
            extracted = extract_year(query)
            query = extracted["cleaned_query"]
            year = extracted["year"]

        hits = _search_rt(query, year=year)

        if not hits:
            self.send_privmsg(cmd.channel, "No results found.")
            return
        
        first_result = hits[0]
        formatted_result = _format(first_result)

        self.send_privmsg(cmd.channel, formatted_result)

    except Exception as e:
        self.send_privmsg(cmd.channel, "Unexpected error occurred.")
        log_err(e)
