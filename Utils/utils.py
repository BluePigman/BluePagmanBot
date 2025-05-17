import requests
import re
import config
import time
from typing import Dict
import json
from bs4 import BeautifulSoup
from typing import Any
import google.generativeai as genai
from groq import Groq

# --- Chat Utilities ---

def fetch_cmd_data(self, message: dict) -> dict:
    """
    Extracts key fields from a message dict and instance attributes, returning them in a new dict:
      - username: str — display name prefixed with '@'
      - channel: str — channel name
      - params: any — botCommandParams from the message
      - nick: str — sender's nickname
      - state: dict — current cooldown state from self
      - cooldown: int — cooldown duration from self
    """
    return {
        "username": f"@{message['tags']['display-name']}",
        "channel": message['command']['channel'],
        "params": message['command']['botCommandParams'],
        "nick": message['source']['nick'],
        "state": self.state,
        "cooldown": self.cooldown
    }

def check_cooldown(state: Dict[str, float], nick: str, cooldown: float) -> bool:
    """
    Returns True if the user is not in cooldown and updates their timestamp.
    Returns False if still in cooldown.
    """
    if nick not in state:
        allowed = True
    else:
        allowed = (time.time() - state[nick]) > cooldown

    if allowed:
        state[nick] = time.time()
        return True
    
    return False

def clean_str(text: str, remove: list[str] = []) -> str:
    """
    Normalize whitespace and optionally remove specified characters.
    """
    if remove:
        chars = ''.join(remove)
        table = str.maketrans('', '', chars)
        text = text.translate(table)
    return re.sub(r'\s+', ' ', text).strip()

CHUNK_SIZE = 495

def chunk_str(text: str, chunk_size: int = CHUNK_SIZE) -> list[str]:
    """
    Split text into chunks of size chunk_size.
    """
    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

def send_chunks(send_func, channel, text: str, chunk_size: int = CHUNK_SIZE) -> None:
    """
    Send text in chunks of size chunk_size to channel.
    """
    chunks = chunk_str(text, chunk_size)
    for chunk in chunks:
        send_func(channel, chunk)
        time.sleep(1)



# --- Proxy HTTP Requests ---

HEADERS = {'User-agent': 'BluePagmanBot'}
TIMEOUT = 10

def proxy_get_request(url: str, headers=HEADERS, timeout=TIMEOUT) -> requests.Response:
    """
    Perform GET request through proxy if configured.
    """
    target_url = url

    if config.PROXY:
        target_url = config.PROXY
        headers["url"] = url

    res = requests.get(target_url, headers=headers, timeout=(timeout, timeout))
    return res

def proxy_post_request(url: str, data=None, json=None, headers=HEADERS, timeout=TIMEOUT) -> requests.Response:
    """
    Perform POST request through proxy if configured.
    """
    target_url = url

    if config.PROXY:
        target_url = config.PROXY
        headers["url"] = url

    res = requests.post(target_url, data=data, json=json, headers=headers, timeout=timeout)
    return res

def parse_str(data: str, kind: str) -> Any:
    """
    Parse the input string as either JSON or HTML.
    """
    if kind == "json":
        return json.loads(data)

    if kind == "html":
        return BeautifulSoup(data, "lxml")

    raise ValueError("kind must be 'json' or 'html'")



# --- LLM Generation Utilities ---

def gemini_generate(request: str | dict, model) -> list[str]:
    """
    Generate content using the model with optional grounding.
    Accepts request as either a string or dict with keys:
    {
        "prompt": str,
        "grounded": bool,
        "grounding_text": str or list[str]
    }
    model: object with generate_content method
    Returns generated text.
    """
    genai.configure(api_key=config.GOOGLE_API_KEY)
    try:
        if isinstance(request, str):
            prompt = request
            grounded = False
            grounding_text = None
        else:
            prompt = request.get("prompt", "")
            grounded = request.get("grounded", False)
            grounding_text = request.get("grounding_text", None)

        if grounded and grounding_text:
            if isinstance(grounding_text, list):
                grounding_text = "\n\n".join(grounding_text)
            full_prompt = f"{prompt}\n\n{grounding_text}"
        else:
            full_prompt = prompt

        response_text = model.generate_content(full_prompt, stream=False).text
        return response_text

    except Exception as e:
        print(e)
        return ["Error: ", str(e)]

def groq_generate(request: dict, client) -> str:
    """
    Generate content using the client with customizable parameters and optional grounding.
    Accepts request as dict with keys:
    {
        "prompt": str,
        "model": str,
        "temperature": float,
        "max_tokens": int,
        "top_p": float,
        "stream": bool,
        "stop": list or None,
        "system_message": str,
        "grounded": bool,
        "grounding_text": str or list[str]
    }
    client: API client object
    Returns generated text.
    """
    client = Groq(api_key=config.GROQ_API_KEY)
    try:
        prompt = request.get("prompt", "")
        grounded = request.get("grounded", False)
        grounding_text = request.get("grounding_text", None)

        if grounded and grounding_text:
            if isinstance(grounding_text, list):
                grounding_text = "\n\n".join(grounding_text)
            prompt = f"{prompt}\n\n{grounding_text}"

        model = request.get("model")
        temperature = request.get("temperature")
        max_tokens = request.get("max_tokens")
        top_p = request.get("top_p")
        stream = request.get("stream")
        stop = request.get("stop")
        system_message = request.get("system_message")

        response_text = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
            max_completion_tokens=max_tokens,
            top_p=top_p,
            stream=stream,
            stop=stop,
        ).choices[0].message.content

        return response_text
    except Exception as e:
        print(e)
        return None
