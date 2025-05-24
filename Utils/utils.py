import config
import os, requests, re, base64, time, json, sqlite3, tempfile
from bs4 import BeautifulSoup
from typing import Any, Dict, List, Union
import google.generativeai as genai_text
from google import genai as genai_image
from google.genai import types
from groq import Groq
from dataclasses import dataclass

# --- Chat Utilities ---

@dataclass
class CmdData:
    username: str
    channel: str
    params: Any
    args: Dict[str, str]
    nick: str
    state: Dict
    cooldown: int

def fetch_cmd_data(self, message: dict, with_args: bool = False) -> CmdData:
    """
    Extracts key fields from a message dict and instance attributes,
    returning them as a CmdData object for structured, type-safe access:
      - username: str — display name prefixed with '@'
      - channel: str — channel name
      - params: any — full botCommandParams or first token (if with_args=True)
      - args: dict — tokens in arg_name:arg_value format (if with_args=True)
      - nick: str — sender's nickname
      - state: dict — current cooldown state from self
      - cooldown: int — cooldown duration from self
    """
    raw = message['command']['botCommandParams']
    if isinstance(raw, str):
        raw = raw.replace('\U000E0000', '')

    params, args = raw, {}

    if with_args and raw:
        parts = raw.split()
        if parts:
            params, *arg_parts = parts
            args = {
                k: v for k, v in (a.split(":", 1) for a in arg_parts if ":" in a)
            }
        else:
            params, args = None, {}

    return CmdData(
        username=f"@{message['tags']['display-name']}",
        channel=message['command']['channel'],
        params=params,
        args=args,
        nick=message['source']['nick'],
        state=self.state,
        cooldown=self.cooldown,
    )

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
    Split text into chunks of words where each chunk's total length (including spaces) 
    does not exceed chunk_size. If adding a word would exceed the limit, start a new chunk.
    """
    words = text.split()
    chunks = []
    current = []

    for word in words:
        if sum(len(w) for w in current) + len(current) + len(word) > chunk_size:
            chunks.append(' '.join(current))
            current = [word]
        else:
            current.append(word)

    if current:
        chunks.append(' '.join(current))

    return chunks

def send_chunks(send_func, channel, text: str, chunk_size: int = CHUNK_SIZE) -> None:
    """
    Send text in chunks of size chunk_size to channel.
    """
    chunks = chunk_str(text, chunk_size)
    for chunk in chunks:
        send_func(channel, chunk)
        time.sleep(1)



# --- File Utilities ---

def upload_to_kappa(filepath: str, ext: str, timeout: int = 60) -> str | None:
    """
    Uploads a file to kappa.lol and returns the direct link. None if the file is not found or upload fails.
    """
    mime_map = {
        "mp4": "video/mp4",
        "mov": "video/mp4",
        "webm": "video/webm",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "gif": "image/gif",
        "png": "image/png",
    }
    content_type = mime_map.get(ext.lower(), "application/octet-stream")
    filename = f"upload.{ext}"
    
    print(f"Uploading {filename} as {content_type} to kappa.lol from {filepath}...")
    try:
        with open(filepath, "rb") as f_video:
            files = {
                'file': (filename, f_video, content_type)
            }
            res = proxy_request("POST", 'https://kappa.lol/api/upload', files=files, timeout=timeout)
        
        res.raise_for_status()
        data = res.json()
        link = data.get("link", "upload failed")
        if link != "upload failed":
            os.remove(filepath)
        print(f"Upload res link: {link}")
        return link

    except FileNotFoundError:
        print(f"Upload error: File not found at {filepath}")
        return None

    except Exception as e:
        print(f"Upload error: {e}")
        return None

def download_bytes(file_url: str) -> bytes | None:
    """Download raw bytes from the given URL, returning None on failure."""
    try:
        res = proxy_request("GET", file_url)
        res.raise_for_status()
        print(f"Downloaded {len(res.content)} bytes")
        return res.content
    except Exception as e:
        print(f"Download error: {e}")
        return None



# --- Proxy HTTP Requests ---

HEADERS = {'User-agent': 'BluePagmanBot'}
TIMEOUT = 10

def proxy_request(method: str, url: str, headers=HEADERS, timeout=TIMEOUT, bypass_proxy=False, **kwargs) -> requests.Response:
    """
    Perform HTTP request with given method through proxy if configured.
    Supports additional requests parameters via kwargs.
    """
    target_url = url
    if config.PROXY and not bypass_proxy:
        target_url = config.PROXY
        headers["url"] = url
    res = requests.request(method, target_url, headers=headers, timeout=(timeout, timeout), **kwargs)

    return res

def fetch_firefox_cookies(domains: List[str] = [], as_netscape: bool = False) -> Union[str, Dict[str, str]]:
    """
    Fetch Firefox cookies for given domains. If no domains are provided, returns all cookies.

    Args:
    domains (List[str]): Domains to filter.
    as_netscape (bool): Return Netscape-format file if True, else dict.

    Returns:
    Union[str, Dict[str, str]]: File path or cookie dict.
    
    Raises:
    Exception: If FIREFOX_COOKIES_PATH is not set in config.
    """
    db_path = getattr(config, 'FIREFOX_COOKIES_PATH', None)
    if not db_path:
        raise Exception("Firefox cookies path not set in config")

    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()

        if domains:
            where_clause = " OR ".join(["host LIKE ?" for _ in domains])
            params = [f"%{d}%" for d in domains]
        else:
            where_clause = "1"
            params = []

        cur.execute(f"""
            SELECT host, path, isSecure, expiry, name, value
            FROM moz_cookies
            WHERE {where_clause}
        """, params)

        rows = cur.fetchall()

    if as_netscape:
        tmp = tempfile.NamedTemporaryFile(delete=False, mode="w", suffix=".txt")
        tmp.write("# Netscape HTTP Cookie File\n")
        for host, path, is_sec, exp, name, val in rows:
            tmp.write(
                f"{host}\t{'TRUE' if host.startswith('.') else 'FALSE'}\t"
                f"{path}\t{'TRUE' if is_sec else 'FALSE'}\t"
                f"{exp or 0}\t{name}\t{val}\n"
            )
        tmp.close()
        return tmp.name

    cookie_dict = {name: val for _, _, _, _, name, val in rows}
    return cookie_dict

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

def gemini_generate(request: str | dict, model) -> str | list[str]:
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
    genai_text.configure(api_key=config.GOOGLE_API_KEY)
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

GEMINI_IMAGE_MODEL = "gemini-2.0-flash-exp-image-generation"

def gemini_generate_image(prompt: str, image_model: str = GEMINI_IMAGE_MODEL) -> str | None:
    """
    Generate an image from a text prompt using Gemini model.
    Returns the file path of the saved image or None if generation fails.
    """
    client = genai_image.Client(api_key=config.GOOGLE_API_KEY)

    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=prompt)],
        )
    ]
    generate_config = types.GenerateContentConfig(
        response_modalities=["image", "text"],
        response_mime_type="text/plain",
    )
    try:
        stream = client.models.generate_content_stream(
            model=image_model,
            contents=contents,
            config=generate_config,
        )
        for chunk in stream:
            c = chunk.candidates
            if not c or not c[0].content or not c[0].content.parts or not c[0].content.parts[0].inline_data:
                continue
            inline_data = c[0].content.parts[0].inline_data
            img_bytes = (
                base64.b64decode(inline_data.data)
                if inline_data.data.startswith(b'iVBORw')
                else inline_data.data
            )
            
            image_filepath = None
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
                temp_file.write(img_bytes)
                image_filepath = temp_file.name

            return image_filepath

        return None
    except Exception as e:
        print(e)
        return None

def groq_generate(request: dict, client_opts: dict | None = None) -> str | None:
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
    client_opts (dict): Optional Groq client settings:
    {
        "base_url": str | URL | None,
        "timeout": float | Timeout | None,
        "max_retries": int,
        "default_headers": Mapping[str, str] | None,
        "default_query": Mapping[str, object] | None,
        "http_client": Client | None,
        "_strict_response_validation": bool
    }
    Returns generated text.
    """
    client_opts = client_opts or {}
    client = Groq(api_key=config.GROQ_API_KEY, **client_opts)

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
