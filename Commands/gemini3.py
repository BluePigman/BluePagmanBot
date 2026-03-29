from datetime import datetime
from urllib.parse import urlencode, unquote, urlparse
from itertools import zip_longest
import re, html2text
from google import genai
from google.genai import types
from Utils.utils import (
    proxy_request,
    clean_str,
    send_chunks,
    fetch_cmd_data,
    gemini_generate,
    check_cooldown,
    parse_str
)

MODEL_NAME = "gemini-flash-lite-latest"
GENERATION_CONFIG = {
    "max_output_tokens": 400,
    "temperature": 0.3,
    "top_p": 0.95,
    "system_instruction": [
        types.Part.from_text(text="Please provide a short, concise response with enough detail. Do not use LaTeX or Markdown formatting in your response. Do not ask the user follow up questions, because you are intended to provide a single response with no history and are not expected any follow up prompts. Answer should be at most 600 characters.")
    ]
}

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://example.com",
}

def fetch_and_parse_html(url):
    try:
        res = proxy_request("GET", url, headers=headers)
        if res:
            print(f"fetch_and_parse_html: Status {res.status_code} for {url}")
            if res.status_code == 429:
                print(f"fetch_and_parse_html: RATE LIMIT (429) hit for {url}")
        else:
            print(f"fetch_and_parse_html: No response object returned for {url}")

        if not res or not res.text:
            print(f"fetch_and_parse_html: Empty response from {url}")
            return None

        return parse_str(res.text, "html")

    except Exception as e:
        print(f"fetch_and_parse_html: Error fetching/parsing {url}: {e}")
        return None
 
def get_duckduckgo_results(query):
    url = "https://lite.duckduckgo.com/lite/?" + urlencode({"q": query})

    soup = fetch_and_parse_html(url)
    if not soup:
        print(f"get_duckduckgo_results: No soup returned for query: {query}")
        return []

    a_elements = soup.select('.result-link')
    if not a_elements:
        print(f"get_duckduckgo_results: No target elements (.result-link) found in HTML for query: {query}")
    else:
        print(f"get_duckduckgo_results: Found {len(a_elements)} result links for query: {query}")
    urls = []

    for a in a_elements:
        try:
            decoded_href = unquote(a['href'])
            match = re.search(r"http.*?(?=&)", decoded_href)
            url = match.group(0) if match else None
            if not url or "ad_domain=" in url:
                continue
            urls.append(url)
        except Exception as e:
            print(f"[Error] {e}")

    return urls


def get_wikipedia_snippet(query):
    try:
        ddg_results = get_duckduckgo_results(query + " site:wikipedia.org")

        if not ddg_results or not isinstance(ddg_results, list):
            return

        path = urlparse(ddg_results[0]).path
        if not path.startswith('/wiki/'):
            return
        title = path.split('/wiki/')[-1]

        url = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "parse",
            "page": title,
            "format": "json",
            "origin": "*"
        }
        res = proxy_request("GET", url, params=params)
        if res:
            print(f"get_wikipedia_snippet: Status {res.status_code} for {url}")
            if res.status_code == 429:
                print(f"get_wikipedia_snippet: RATE LIMIT (429) hit for {url}")
        else:
            print(f"get_wikipedia_snippet: No response object returned for {url}")

        if not res or res.status_code != 200:
            print(f"get_wikipedia_snippet: Invalid response or status code != 200 for {url}")
            return

        json_data = res.json()
        text = json_data.get("parse", {}).get("text", {}).get("*", "")
        soup = parse_str(text, "html")
        if soup is None:
            return

        content = []
        for elem in soup.find_all(['p', 'h2']):
            if elem.name == 'h2':
                break
            if elem.name == 'p':
                content.append(str(elem))

        intro_html = "".join(content)

        text_maker = html2text.HTML2Text()
        text_maker.ignore_links = True
        text_maker.ignore_emphasis = True
        text_maker.ignore_images = True
        text_maker.ignore_tables = True
        text_maker.body_width = 0

        snippet = text_maker.handle(intro_html).strip()

        return snippet

    except Exception as e:
        print(f"[Error] {e}")
        return

def querify(prompt):
    model_name = "gemma-3n-e4b-it"
    config = { "max_output_tokens": 400, "temperature": 0.3 }
    prompt = f"Convert into a keyword Google search query if needed. Return only the resulting query, without quotes or any extra text: {prompt}"
    result = gemini_generate(prompt, model_name, config)
    if not result:
        return
    
    return result

def get_body_content(url):
    soup = fetch_and_parse_html(url)
    if not soup:
        return ""

    if not soup.body:
        print("get_body_content: <body> tag not found.")
        return ""

    text = soup.body.get_text(" ", strip=True)
    
    cf_messages = [
        "JavaScript is disabled",
        "verify that you're not a robot",
        "Enable JavaScript and then reload",
        "Checking your browser before accessing"
    ]
    
    if any(msg in text for msg in cf_messages):
        print(f"get_body_content: Bot protection detected for {url}, skipping")
        return ""

    return text

def get_grounding_data(prompt, count=2):
    blocked_domains = {'facebook.com', 'youtube.com', 'reddit.com', 'instagram.com'}
    modifiers = ' ' + ' '.join(f'-site:{domain}' for domain in blocked_domains)

    normal_urls = get_duckduckgo_results(prompt + modifiers)
    if normal_urls:
        print("Normal URLs:", normal_urls)

    query_urls = []
    query = querify(prompt)

    if query and query.strip() != prompt:
        print("Query:", query)
        query_urls = get_duckduckgo_results(query + modifiers)
        if query_urls:
            print("Query URLs:", query_urls)

    valid_urls = []
    contents = []

    seen = set()
    for group_idx, group in enumerate(zip_longest(normal_urls, query_urls)):
        print(f"Group {group_idx}: {group}")
        for url_idx, url in enumerate(group):
            print(f"  URL {url_idx}: {url}")
            if not url:
                print("    Skipped: URL is None or empty")
                continue
            if url in seen:
                print("    Skipped: URL already seen")
                continue
            domain = urlparse(url).netloc
            print(f"    Domain: {domain}")
            if any(blocked_domain in url for blocked_domain in blocked_domains):
                print("    Skipped: Domain blocked")
                continue
            content = get_body_content(url)
            if not content:
                print("    Skipped: No content retrieved")
                continue
            seen.add(url)
            valid_urls.append(url)
            contents.append(content)
            print(f"    Added URL, total valid URLs: {len(valid_urls)}")
            if len(valid_urls) == count:
                print("    Reached count limit, breaking")
                break
        if len(valid_urls) == count:
            break

    wikipedia_snippet = get_wikipedia_snippet(prompt)
    if wikipedia_snippet:
        print(f"Wikipedia Snippet: {wikipedia_snippet[:300]}\n")

    if not valid_urls and not wikipedia_snippet:
        return None

    combined_content = "\n".join(contents)
    return {
        'body_content': combined_content,
        'wikipedia_snippet': wikipedia_snippet,
        'valid_urls': valid_urls
    }

def reply_with_grounded_gemini(self, message):
    cmd = fetch_cmd_data(self, message)
    
    if not check_cooldown(cmd.state, cmd.nick, cmd.cooldown):
        return
    
    if not cmd.params:
        m = (
            f"{cmd.username}, please provide a prompt for Gemini. "
            f"Model: {MODEL_NAME}, temperature: {GENERATION_CONFIG['temperature']}, "
            f"top_p: {GENERATION_CONFIG['top_p']}"
        )
        self.send_privmsg(cmd.channel, m)
        return

    prompt = cmd.params.strip()
    try:
        utc_date_time = datetime.now().strftime("%A %d %B %Y %I:%M %p UTC")
        
        grounding_data = get_grounding_data(prompt) or {}

        valid_urls = grounding_data.get('valid_urls', [])
        wikipedia_snippet = grounding_data.get('wikipedia_snippet')

        is_grounded = bool(valid_urls) or bool(wikipedia_snippet)
            
        if is_grounded:
            grounding_text = f"""Today is {utc_date_time}.
        Use the provided information to help answer the prompt. 
        If you use this information, do so seamlessly as if it were your own knowledge. 
        Do not mention that you have been provided with any text or information and do not allude to it in any way.
        Just interpret the user's request and answer directly:
        {wikipedia_snippet or ''}
        {grounding_data.get('body_content', '')}"""
        else:
            grounding_text = None

        result = gemini_generate({
            "prompt": prompt,
            "grounded": is_grounded,
            "grounding_text": grounding_text
        }, MODEL_NAME, GENERATION_CONFIG)

        if not result:
            self.send_privmsg(cmd.channel, "Failed to generate a response. Please try again later.")
            return
        
        clean_result = clean_str(result, ['`', '*'])
        send_chunks(self.send_privmsg, cmd.channel, clean_result)
        if valid_urls:
            self.send_privmsg(cmd.channel, f"📝 Source(s): {' | '.join(valid_urls)}")

    except Exception as e:
        print(f"[Error] {e}")
        self.send_privmsg(cmd.channel, "Failed to send a response. Please try again later.")
        return