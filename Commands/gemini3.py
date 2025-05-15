import time
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlencode, unquote
import re
import google.generativeai as genai
import config

TIMEOUT = 10

genai.configure(api_key=config.GOOGLE_API_KEY)

model_name = "gemini-2.0-flash-lite"

generation_config = {
    "max_output_tokens": 400,
    "temperature": 0.5,
    "top_p": 0.95,
}

system_instruction = [
    """Please always provide a short and concise response. Do not ask the user follow up questions, 
    because you are intended to provide a single response with no history and are not expected
    any follow up prompts. Answer should be at most 990 characters."""
]

utc_date_time = datetime.now().strftime("%d %B %Y %I:%M %p UTC")

model = genai.GenerativeModel(
    model_name=model_name,
    generation_config=generation_config,
    system_instruction=system_instruction
)

def get_duckduckgo_results(query):
    url = "https://lite.duckduckgo.com/lite/?" + urlencode({"q": query})
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        if config.PROXY:
            req = requests.get(config.PROXY, headers={"url": url, **headers}, timeout=TIMEOUT)
        else:   
            req = requests.get(url, headers=headers, timeout=TIMEOUT)
    except requests.RequestException as e:
        print(f"get_duckduckgo_results: Request failed: {e}")
        return []

    if not req or not req.text:
        print("get_duckduckgo_results: No response or empty body from DuckDuckGo.")
        return []

    try:
        soup = BeautifulSoup(req.text, 'html.parser')
    except Exception as e:
        print(f"get_duckduckgo_results: Error parsing HTML: {e}")
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

def get_body_content(url):
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        if config.PROXY:
            req = requests.get(config.PROXY, headers={"url": url, **headers}, timeout=TIMEOUT)
        else:
            req = requests.get(url, headers=headers, timeout=TIMEOUT)
    except requests.RequestException as e:
        print(f"get_body_content: Request failed: {e}")
        return ""

    if not req or not req.text:
        print(f"get_body_content: No response or empty body from {url}.")
        return ""

    try:
        soup = BeautifulSoup(req.text, 'html.parser')
    except Exception as e:
        print(f"get_body_content: Error parsing HTML: {e}")
        return ""

    if not soup.body:
        print("get_body_content: <body> tag not found.")
        return ""

    return soup.body.get_text(" ", strip=True)

def get_grounding_data(prompt, count=2):
    urls = get_duckduckgo_results(prompt)
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

def generate(prompt, grounding_text=None) -> list[str]:
    try:
        if grounding_text:
            full_prompt = f"{prompt}\n\nToday is {utc_date_time}.\n\nUse this to ground your response (Don't mention that I provided you with a text/document/article/context for your response under any circumstance. Answer as if you know this information):\n{grounding_text}"
        else:
            full_prompt = prompt

        response = model.generate_content(full_prompt, stream=False).text.replace('\n', ' ').replace('*', ' ')
        n = 495
        return [response[i:i+n] for i in range(0, len(response), n)]
    except Exception as e:
        print(e)
        return ["Error: ", str(e)]

def reply_with_grounded_gemini(self, message):
    username = f"@{message['tags']['display-name']}"
    channel = message['command']['channel']
    params = message['command']['botCommandParams']
    nick = message['source']['nick']

    if nick not in self.state or time.time() - self.state[nick] > self.cooldown:
        self.state[nick] = time.time()

    if not params:
        m = f"{username}, please provide a prompt for Gemini. Model: {model_name}, temperature: {generation_config['temperature']}, top_p: {generation_config['top_p']}"
        self.send_privmsg(channel, m)
        return

    prompt = params.strip()
    print(prompt)
    self.send_privmsg(channel, "Searching DuckDuckGo, please wait..")

    grounding_data = get_grounding_data(prompt)
    body_content = grounding_data['body_content']
    duck_urls = grounding_data['duck_urls']

    result = generate(prompt, grounding_text=body_content)
    prefix = "🔎 Grounded: " if body_content.strip() else "Not Grounded: "

    if "Error" in result[0]:
        self.send_privmsg(channel, f"Failed to generate a response. Please try again later.")
        return

    for i, m in enumerate(result):
        if i == 0:
            m = prefix + m
        if i == len(result) - 1 and duck_urls:
            m += f" 📝 Source(s): {' | '.join(duck_urls)}"
        self.send_privmsg(channel, m)
        time.sleep(1)
