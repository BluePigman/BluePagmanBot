from datetime import datetime
from urllib.parse import urlencode, unquote, urlparse
from itertools import zip_longest
import re, html2text
import google.generativeai as genai
from Utils.utils import (
    proxy_request,
    clean_str,
    send_chunks,
    fetch_cmd_data,
    gemini_generate,
    check_cooldown,
    parse_str
)

model = genai.GenerativeModel(
    model_name="gemini-2.0-flash-lite",
    generation_config={
        "max_output_tokens": 400,
        "temperature": 0.3,
        "top_p": 0.95,
    },
    system_instruction=[
        "Please provide a short, concise response with enough detail. Do not ask the user follow up questions, because you are intended to provide a single response with no history and are not expected any follow up prompts. Answer should be at most 990 characters."
    ]
)

def fetch_and_parse_html(url):
    try:
        res = proxy_request("GET", url)
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
        return []

    a_elements = soup.select('.result-link')
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

def get_google_lucky(query):
    params = {'q': query, 'btnI': "I'm Feeling Lucky"}
    query_string = urlencode(params)
    url = f"https://www.google.com/search?{query_string}"

    soup = fetch_and_parse_html(url)

    if not soup:
        return
    
    link = soup.find('a', href=True)

    return link['href'] if link else None

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
        if not res or res.status_code != 200:
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
    gemma_model = genai.GenerativeModel(
        model_name="gemma-3n-e4b-it",
        generation_config={ "max_output_tokens": 400, "temperature": 0.3 }
    )
    prompt = f"Convert into a keyword Google search query if needed. Return only the resulting query, without quotes or any extra text: {prompt}"
    result = gemini_generate(prompt, gemma_model)
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

    return soup.body.get_text(" ", strip=True)

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

    google_lucky_url = get_google_lucky(prompt)
    google_urls = [google_lucky_url] if google_lucky_url else []
    if google_lucky_url:
        print("Google URL:", google_lucky_url)

    if not (normal_urls or query_urls or google_urls):
        return

    valid_urls = []
    contents = []

    seen = set()
    for group_idx, group in enumerate(zip_longest(normal_urls, query_urls, google_urls)):
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
            f"Model: {model.model_name}, temperature: {model._generation_config['temperature']}, "
            f"top_p: {model._generation_config['top_p']}"
        )
        self.send_privmsg(cmd.channel, m)
        return

    prompt = cmd.params.strip()
    try:
        utc_date_time = datetime.now().strftime("%A %d %B %Y %I:%M %p UTC")
        
        grounding_data = get_grounding_data(prompt)

        if not grounding_data:
            self.send_privmsg(cmd.channel, "No results found for the query.")
            return

        valid_urls = grounding_data['valid_urls']
        grounding_text = (
            f"Today is {utc_date_time}.\n\n"
            "Use what's relevant of this text to inform your response to the prompt above (Don't mention that I provided you with a text/document/article/context for your response under any circumstance. Answer as if you know this information):\n"
            f"{grounding_data['wikipedia_snippet']}\n"
            f"{grounding_data['body_content']}"
        )

        is_grounded = bool(valid_urls)

        result = gemini_generate({
            "prompt": prompt,
            "grounded": is_grounded,
            "grounding_text": grounding_text
        }, model)

        if "Error" in result[0]:
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