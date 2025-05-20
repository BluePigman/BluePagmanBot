import time
from datetime import datetime
from urllib.parse import urlencode, unquote
import re
import google.generativeai as genai
import config
from Utils.utils import (
    proxy_get_request,
    clean_str,
    send_chunks,
    fetch_cmd_data,
    gemini_generate,
    check_cooldown,
    parse_str,
)

utc_date_time = datetime.now().strftime("%A %d %B %Y %I:%M %p UTC")

model = genai.GenerativeModel(
    model_name="gemini-2.0-flash-lite",
    generation_config={
        "max_output_tokens": 400,
        "temperature": 0.5,
        "top_p": 0.95,
    },
    system_instruction=[
        "Please always provide a short and concise response. Do not ask the user follow up questions, because you are intended to provide a singlen response with no history and are not expected any follow up prompts. Answer should be at most 990 characters."
    ]
)

def fetch_and_parse_html(url):
    try:
        res = proxy_get_request(url)
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

    print(urls)
    return urls

def get_google_lucky(query):
    params = {'q': query, 'btnI': "I'm Feeling Lucky"}
    query_string = urlencode(params)
    url = f"https://www.google.com/search?{query_string}"

    soup = fetch_and_parse_html(url)
    
    if not soup:
        return None

    link = soup.find('a', href=True)
    return link['href'] if link else None

def get_body_content(url):
    soup = fetch_and_parse_html(url)
    if not soup:
        return ""

    if not soup.body:
        print("get_body_content: <body> tag not found.")
        return ""

    return soup.body.get_text(" ", strip=True)

def get_grounding_data(prompt, count=2):
    urls = get_duckduckgo_results(prompt)
    google_lucky_url = get_google_lucky(prompt)
    if google_lucky_url:
        urls.insert(0, google_lucky_url)
    contents = []
    valid_urls = []

    for url in urls:
        content = get_body_content(url)
        if content:
            valid_urls.append(url)
            contents.append(content)
        if len(valid_urls) == count:
            break

    combined_content = "\n".join(contents)
    return {'body_content': combined_content, 'duck_urls': valid_urls}

def reply_with_grounded_gemini(self, message):
    cmd_data = fetch_cmd_data(self, message)
    username, channel, params, nick, state, cooldown = cmd_data.values()

    check_cooldown(state, nick, cooldown)

    if not params:
        m = (
            f"{username}, please provide a prompt for Gemini. "
            f"Model: {model.model_name}, temperature: {model._generation_config['temperature']}, "
            f"top_p: {model._generation_config['top_p']}"
        )

        self.send_privmsg(channel, m)
        return

    prompt = params.strip()
    print(prompt)
    self.send_privmsg(channel, "Searching DuckDuckGo, please wait..")

    grounding_data = get_grounding_data(prompt)
    duck_urls = grounding_data['duck_urls']
    grounding_text = (
        f"Today is {utc_date_time}.\n\n"
        "Use this text to ground your response (Don't mention that I provided you with a text/"
        "document/article/context for your response under any circumstance. Answer as if you know this information):\n"
        f"{grounding_data['body_content']}"
    )

    is_grounded = bool(duck_urls)

    result = gemini_generate({
        "prompt": prompt,
        "grounded": is_grounded,
        "grounding_text": grounding_text
    }, model)

    if "Error" in result[0]:
        self.send_privmsg(channel, f"Failed to generate a response. Please try again later.")
        return

    try:
        clean_result = clean_str(result, ['`', '*'])
        send_chunks(self.send_privmsg, channel, clean_result)
        if duck_urls:
            self.send_privmsg(channel, f"📝 Source(s): {' | '.join(duck_urls)}")
    except Exception as e:
        print(f"[Error] {e}")
        self.send_privmsg(channel, f"Failed to send a response. Please try again later")
