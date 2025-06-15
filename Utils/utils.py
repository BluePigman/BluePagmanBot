from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urlencode, urlparse, quote_plus
from typing import Any, Dict, List, Union
import google.generativeai as genai_text
from google import genai as genai_image
from google.genai import types
from groq import Groq
from dataclasses import dataclass
import config, os, requests, re, base64, time, json, sqlite3, tempfile, traceback, inspect, mimetypes, uuid

# --- Error Logging ---

def log_err(e: Exception) -> None: 
    """Prints detailed information about an exception to the console, including type, message, args, and traceback."""
    try:
        caller = inspect.stack()[1].function
        print(f"\033[31mError in function: [{caller}]\033[0m")
        print(f"Type: {type(e).__name__}")
        print(f"Message: {e}")
        print(f"Args: {e.args}")
        print("Traceback:")
        traceback.print_tb(e.__traceback__)
    except Exception as ex:
        print("Error while printing exception details:")
        print(f"{type(ex).__name__}: {ex}")

def msg_err(send_func: callable, channel: str, e: Exception) -> None:
    """Sends a simplified error message to a channel."""
    try:
        msg = f"Error occurred: {str(e)}"
        send_func(channel, msg)
    except Exception as ex:
        log_err(ex)



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

def fetch_cmd_data(self, message: dict, split_params: bool = False, arg_types: dict = None) -> CmdData:
    """
    Extracts key fields from a message dict and instance attributes,
    returning them as a CmdData object for structured, type-safe access:
      - nick: str — sender's username
      - username: str — sender's username prefixed with '@'
      - channel: str — channel name
      - params: list|str — full botCommandParams with all arguments removed (split into words if split_params=True)
      - args: dict — parsed arguments in -key value or -flag format according to arg_types
      - state: dict — current cooldown state from self
      - cooldown: int — cooldown duration from self
    """
    raw = message['command']['botCommandParams']
    if isinstance(raw, str):
        raw = raw.replace('\U000E0000', '')
    else:
        raw = ''

    args = {}
    if arg_types:
        remaining = raw
        for key, typ in arg_types.items():
            pattern = {
                bool: re.compile(fr'-{key}\b'),
                str: re.compile(fr'-{key}\s+((?:(?! -\w).)+)', re.DOTALL),
                int: re.compile(fr'-{key}\s+(-?\d+)\b'),
                float: re.compile(fr'-{key}\s+(-?\d+(?:\.\d+)?)\b')
            }[typ]

            match = pattern.search(remaining)
            if not match:
                continue

            try:
                val = True if typ is bool else typ(match.group(1).strip())
            except:
                continue

            args[key] = val
            start, end = match.span()
            remaining = remaining[:start] + ' ' * (end - start) + remaining[end:]

        raw = ' '.join(remaining.split())

    params = raw.split() if split_params else raw

    return CmdData(
        nick=message['source']['nick'],
        username=f"@{message['tags']['display-name']}",
        channel=message['command']['channel'],
        params=params,
        args=args,
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

def clean_str(text: str, remove: list[str] = None) -> str:
    """
    Normalize whitespace and optionally remove specified characters.
    """
    if remove:
        text = text.translate(str.maketrans('', '', ''.join(remove)))
    return re.sub(r'\s+', ' ', text).strip()


def encode_str(input_text):
    return quote_plus(input_text)

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

def send_chunks(send_func: callable, channel, text: str, chunk_size: int = CHUNK_SIZE, delay: float = 1.2) -> None:
    """
    Send text in chunks of size chunk_size to channel, delay is in seconds.
    """
    chunks = chunk_str(text, chunk_size)
    for idx, chunk in enumerate(chunks):
        send_func(channel, chunk)
        if idx < len(chunks) - 1:
            time.sleep(delay)



# --- File Utilities ---

class GenericStorage:
    """
    GenericStorage manages a JSON-backed dictionary stored in a file.

    A subfolder named 'generic_storage' is created inside the system temp directory.
    All storage files are placed inside this folder.
    This isolates storage and allows bulk deletion via delete_all().

    __init__(filename, initial_data=None):
        Initializes storage with the given filename inside the storage folder.
        If initial_data (a dict) is provided, it overwrites the file.
        If the file exists and no initial_data is provided, existing data is preserved.

    _read():
        Reads and returns the entire dictionary from the file.
        Returns an empty dict if file doesn't exist or contains invalid JSON.

    _write(data):
        Writes the given dictionary to the file as JSON.

    set(key, value):
        Adds or updates the value for the given key.
        Overwrites the key if it already exists.

    get(key, default=None):
        Returns the value associated with the key.
        If key not found and default is provided, sets key to default and returns it.

    get_all():
        Returns the entire stored dictionary.

    delete(key):
        Removes the key and its value if the key exists.
        Does nothing if the key does not exist.

    delete_all():
        Deletes the entire 'generic_storage' folder and all contained files.

    has(key):
        Returns True if the key exists in storage, else False.

    keys():
        Returns a list of all keys currently stored.

    values():
        Returns a list of all values currently stored.

    items():
        Returns a list of (key, value) tuples currently stored.

    is_empty():
        Returns True if storage is empty (no keys), else False.
    """
    def __init__(self, filename, initial_data=None):
        self.folder = os.path.join(tempfile.gettempdir(), "generic_storage")
        os.makedirs(self.folder, exist_ok=True)
        self.path = os.path.join(self.folder, filename)
        if initial_data is not None:
            self._write(initial_data)

    def _read(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, "r") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {}
        return {}

    def _write(self, data):
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(data, f)
        except TypeError as e:
            log_err(e)

    def set(self, key, value):
        data = self._read()
        data[key] = value
        self._write(data)

    def get(self, key, default=None):
        data = self._read()
        if key not in data and default is not None:
            data[key] = default
            self._write(data)
        return data.get(key, default)

    def get_all(self):
        return self._read()

    def delete(self, key):
        data = self._read()
        if key in data:
            del data[key]
            self._write(data)

    def delete_all(self):
        if os.path.exists(self.folder):
            for f in os.listdir(self.folder):
                os.remove(os.path.join(self.folder, f))
            os.rmdir(self.folder)

    def has(self, key):
        return key in self._read()

    def keys(self):
        return list(self._read().keys())

    def values(self):
        return list(self._read().values())

    def items(self):
        return list(self._read().items())

    def is_empty(self):
        return not bool(self._read())

def upload_to_kappa(filepath: str, ext: str, delete_file: bool = False, timeout: int = 60) -> str | None:
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
        if link != "upload failed" and delete_file:
            os.remove(filepath)
        print(f"Upload res link: {link}")
        return link

    except FileNotFoundError:
        print(f"Upload error: File not found at {filepath}")
        return None

    except Exception as e:
        print(f"Upload error: {e}")
        log_err(e)
        return None

def download_bytes(file_url: str) -> str | None:
    """Download data from the given URL and return it base64-encoded as a string, or None on failure."""
    try:
        res = proxy_request("GET", file_url)
        res.raise_for_status()
        print(f"Downloaded {len(res.content)} bytes")
        base64_bytes = base64.b64encode(res.content).decode('ascii')

        return base64_bytes

    except Exception as e:
        log_err(e)
        return None



# --- Proxy HTTP Requests ---

HEADERS = {'User-agent': 'BluePagmanBot'}
TIMEOUT = 10

proxy = getattr(config, 'PROXY', None)

def proxy_rotator(proxy: list[str] | str, domain: str) -> str:
    """
    Cycles proxies from a list on repeated calls with the same domain.
    If proxy is not a list, returns it as-is.
    """
    if not isinstance(proxy, list):
        return proxy

    storage = GenericStorage(".proxy_data")
    data = storage.get("proxy_data", {"domain": "", "idx": 0})

    if data["domain"] == domain:
        data["idx"] = (data["idx"] + 1) % len(proxy)
        print("🔄 CYCLING PROXY:", proxy[data["idx"]])
    else:
        data["domain"] = domain

    storage.set("proxy_data", data)

    return proxy[data["idx"]]

def proxy_request(method: str, url: str, headers=None, timeout=TIMEOUT, bypass_proxy=False, session=None, **kwargs) -> requests.Response:
    """
    Perform HTTP request with given method through proxy if configured.
    Supports additional requests parameters via kwargs.
    Optionally accepts a requests.Session object for persistent sessions.
    """
    if headers is None:
        headers = HEADERS.copy()
    else:
        headers = headers.copy()
    
    target_url = url
    if proxy and not bypass_proxy:
        domain = urlparse(url).netloc
        target_url = proxy_rotator(proxy, domain)
        qs = urlencode(kwargs.get("params", {}), doseq=True)
        headers["url"] = f"{url}?{qs}" if qs else url
        kwargs.pop("params", None)

    requester = session or requests
    res = requester.request(method, target_url, headers=headers, timeout=(timeout, timeout), **kwargs)
    
    return res

def fetch_firefox_cookies(domains: List[str] | None = None, as_netscape: bool = False) -> Union[str, Dict[str, str]]:
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
        with tempfile.NamedTemporaryFile(delete=False, mode="w", suffix=".txt") as tmp:
            tmp.write("# Netscape HTTP Cookie File\n")
            for host, path, is_sec, exp, name, val in rows:
                tmp.write(
                    f"{host}\t{'TRUE' if host.startswith('.') else 'FALSE'}\t"
                    f"{path}\t{'TRUE' if is_sec else 'FALSE'}\t"
                    f"{exp or 0}\t{name}\t{val}\n"
                )
            temp_path = tmp.name
        return temp_path

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

def is_url(url):
    """
    Validates a URL with or without http(s) scheme by checking its structure and ensuring
    the top-level domain (TLD) is in the official IANA TLD list, cached locally in 'Data/TLDs.txt'.

    Pattern groups:
    1. One or more subdomains (e.g., 'www.', 'api.')
    2. Top-level domain (TLD) (e.g., 'com', 'org')
    """
    tld_file = Path(__file__).resolve().parent / ".." / "Data" / "TLDs.txt"
    tld_file = tld_file.resolve()

    if os.path.exists(tld_file):
        with open(tld_file, "r") as f:
            lines = f.read().splitlines()
    else:
        res = proxy_request("GET", "https://data.iana.org/TLD/tlds-alpha-by-domain.txt")
        if res.status_code != 200:
            raise RuntimeError(f"Failed to fetch TLD list, status code: {res.status_code}")
        lines = res.text.splitlines()
        os.makedirs(os.path.dirname(tld_file), exist_ok=True)
        with open(tld_file, "w") as f:
            f.write(res.text)

    tlds = {line.lower() for line in lines if line and not line.startswith('#')}
    if not tlds:
        raise RuntimeError("Empty TLD list fetched from IANA")

    unsafe_chars = set(' "\'<>{}|\\^[]`')
    if any(c in url for c in unsafe_chars):
        raise ValueError("URL contains unsafe characters")

    pattern = (
        r'^(?:https?://)?'
        r'([a-z0-9-]+\.)+'
        r'([a-z]{2,})'
        r'(?::\d+)?'
        r'(?:/[^\s]*)?$'
    )
    match = re.match(pattern, url, re.IGNORECASE)
    if not match:
        return False

    tld = match.group(2).lower()
    return tld in tlds



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
        log_err(e)
        return

GEMINI_IMAGE_MODEL = "gemini-2.0-flash-exp-image-generation"

def gemini_generate_image(prompt: str, input_images_b64: list[bytes] | None = None, temperature: float = 1, image_model: str = GEMINI_IMAGE_MODEL) -> str | None:
    """
    Generate an image from a text prompt and optional input images using Gemini model.
    Returns the file path of the saved image or None if generation fails.
    """
    client = genai_image.Client(api_key=config.GOOGLE_API_KEY)

    contents_parts = []
    if input_images_b64:
        for image_b64 in input_images_b64:
            contents_parts.append(
                types.Part.from_bytes(
                    mime_type="image/png",
                    data=base64.b64decode(image_b64),
                )
            )
    contents_parts.append(types.Part.from_text(text=prompt))

    contents = [
        types.Content(
            role="user",
            parts=contents_parts,
        )
    ]

    generate_config = types.GenerateContentConfig(
        response_modalities=["image", "text"],
        response_mime_type="text/plain",
        temperature=temperature,
    )

    try:
        for chunk in client.models.generate_content_stream(
            model=image_model,
            contents=contents,
            config=generate_config,
        ):
            c = chunk.candidates
            if not c or not c[0].content or not c[0].content.parts:
                continue
            inline_data = c[0].content.parts[0].inline_data
            if inline_data and inline_data.data:
                data_buffer = base64.b64decode(inline_data.data) if inline_data.data.startswith(b'iVBORw') else inline_data.data
                file_extension = mimetypes.guess_extension(inline_data.mime_type) or ".png"
                dir_path = os.path.join(tempfile.gettempdir(), "gemini_generated_images")
                os.makedirs(dir_path, exist_ok=True)
                file_name = os.path.join(dir_path, f"generated_image_{uuid.uuid4().hex}{file_extension}")
                with open(file_name, "wb") as f:
                    f.write(data_buffer)

                return file_name

            elif chunk.text:
                print(chunk.text)

        return None

    except Exception as e:
        log_err(e)
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
        log_err(e)
        return None
