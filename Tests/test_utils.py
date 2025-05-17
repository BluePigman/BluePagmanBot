import unittest
from unittest.mock import MagicMock
import time
import re
import requests
import types
import Utils.utils as utils
from bs4 import BeautifulSoup
import json

GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"
SEP = "-" * 50

class TestUtils(unittest.TestCase):

    def setUp(self):
        self.message = {
            "tags": {"display-name": "user1", "room-id": "1234"},
            "command": {"channel": "#channel", "botCommandParams": ["param1"]},
            "source": {"nick": "user1"}
        }
        self.state = {}
        self.cooldown = 1.0
        self.dummy = types.SimpleNamespace(state=self.state, cooldown=self.cooldown)

    def print_result(self, test_name, passed):
        color = GREEN if passed else RED
        status = "PASSED" if passed else "FAILED"
        print(f"{color}{test_name}: {status}{RESET}\n{SEP}\n")

    def test_fetch_cmd_data(self):
        print(f"\n{SEP}\nRunning test: fetch_cmd_data\n{SEP}")
        try:
            result = utils.fetch_cmd_data(self.dummy, self.message)
            print("Extracted data:", result)
            assert result["username"] == "@user1"
            assert result["channel"] == "#channel"
            assert result["params"] == ["param1"]
            assert result["nick"] == "user1"
            assert result["state"] is self.state
            assert result["cooldown"] == self.cooldown
            self.print_result("fetch_cmd_data", True)
        except Exception:
            self.print_result("fetch_cmd_data", False)
            raise

    def test_check_cooldown(self):
        print(f"\n{SEP}\nRunning test: check_cooldown\n{SEP}")
        nick = "user1"
        try:
            allowed = utils.check_cooldown(self.state, nick, self.cooldown)
            print(f"First check (should be True): {allowed}")
            allowed = utils.check_cooldown(self.state, nick, self.cooldown)
            print(f"Second check immediately (should be False): {allowed}")
            time.sleep(self.cooldown)
            allowed = utils.check_cooldown(self.state, nick, self.cooldown)
            print(f"Third check after cooldown (should be True): {allowed}")
            self.print_result("check_cooldown", True)
        except Exception:
            self.print_result("check_cooldown", False)
            raise

    def test_clean_str(self):
        print(f"\n{SEP}\nRunning test: clean_str\n{SEP}")
        try:
            text = "  Hello,  world!  "
            normalized = utils.clean_str(text)
            removed = utils.clean_str(text, remove=[",", "!"])
            print(f"Original: '{text}'")
            print(f"Normalized whitespace: '{normalized}'")
            print(f"Removed ',' and '!': '{removed}'")
            assert normalized == "Hello, world!"
            assert removed == "Hello world"
            self.print_result("clean_str", True)
        except Exception:
            self.print_result("clean_str", False)
            raise

    def test_chunk_str(self):
        print(f"\n{SEP}\nRunning test: chunk_str\n{SEP}")
        try:
            text = "abcdefghij"
            chunks = utils.chunk_str(text, 3)
            print(f"Original text: '{text}'")
            print(f"Chunks (size=3): {chunks}")
            assert chunks == ["abc", "def", "ghi", "j"]
            self.print_result("chunk_str", True)
        except Exception:
            self.print_result("chunk_str", False)
            raise

    def test_send_chunks(self):
        print(f"\n{SEP}\nRunning test: send_chunks\n{SEP}")
        try:
            sent = []
            def fake_send(channel, text):
                sent.append(text)
            text = "abcdefghij"
            utils.send_chunks(fake_send, "#chan", text, chunk_size=3)
            print(f"Sent chunks: {sent}")
            assert sent == ["abc", "def", "ghi", "j"]
            self.print_result("send_chunks", True)
        except Exception:
            self.print_result("send_chunks", False)
            raise

    def test_proxy_get_request(self):
        print(f"\n{SEP}\nRunning test: proxy_get_request\n{SEP}")
        try:
            original_get = requests.get
            requests.get = MagicMock(return_value="GET_RESPONSE")
            utils.config.PROXY = None
            res = utils.proxy_get_request("http://example.com")
            print(f"Response: {res}")
            requests.get.assert_called_with("http://example.com", headers=utils.HEADERS, timeout=(utils.TIMEOUT, utils.TIMEOUT))
            requests.get = original_get
            assert res == "GET_RESPONSE"
            self.print_result("proxy_get_request", True)
        except Exception:
            self.print_result("proxy_get_request", False)
            raise

    def test_proxy_post_request(self):
        print(f"\n{SEP}\nRunning test: proxy_post_request\n{SEP}")
        try:
            original_post = requests.post
            requests.post = MagicMock(return_value="POST_RESPONSE")
            utils.config.PROXY = None
            res = utils.proxy_post_request("http://example.com", data={"x":1})
            print(f"Response: {res}")
            requests.post.assert_called_with("http://example.com", data={"x":1}, json=None, headers=utils.HEADERS, timeout=utils.TIMEOUT)
            requests.post = original_post
            assert res == "POST_RESPONSE"
            self.print_result("proxy_post_request", True)
        except Exception:
            self.print_result("proxy_post_request", False)
            raise

    def test_parse_str(self):
        print(f"\n{SEP}\nRunning test: parse_str\n{SEP}")
        try:
            json_str = '{"key": "value"}'
            html_str = "<html><body><p>test</p></body></html>"
            parsed_json = utils.parse_str(json_str, "json")
            parsed_html = utils.parse_str(html_str, "html")
            print(f"Parsed JSON: {parsed_json}")
            print(f"Parsed HTML: {parsed_html.p.text}")
            assert parsed_json["key"] == "value"
            assert isinstance(parsed_html, BeautifulSoup)
            assert parsed_html.p.text == "test"
            self.print_result("parse_str", True)
        except Exception:
            self.print_result("parse_str", False)
            raise

    def test_gemini_generate(self):
        print(f"\n{SEP}\nRunning test: gemini_generate\n{SEP}")
        try:
            class DummyModel:
                def generate_content(self, prompt, stream):
                    return types.SimpleNamespace(text="response text")
            model = DummyModel()
            out = utils.gemini_generate("hi", model)
            print(f"Output for string prompt: {out}")
            request = {"prompt": "hi", "grounded": True, "grounding_text": ["g1", "g2"]}
            out2 = utils.gemini_generate(request, model)
            print(f"Output for dict prompt with grounding: {out2}")
            assert out == "response text"
            assert out2 == "response text"
            self.print_result("gemini_generate", True)
        except Exception:
            self.print_result("gemini_generate", False)
            raise

    def test_groq_generate(self):
        print(f"\n{SEP}\nRunning test: groq_generate\n{SEP}")
        try:
            class DummyClient:
                class Chat:
                    class Completions:
                        def create(self, **kwargs):
                            class Choice:
                                message = types.SimpleNamespace(content="response text")
                            return types.SimpleNamespace(choices=[Choice()])
                    completions = Completions()
                chat = Chat()
            client = DummyClient()
            request = {
                "prompt": "hello",
                "model": "model1",
                "temperature": 0.5,
                "max_tokens": 50,
                "top_p": 1.0,
                "stream": False,
                "stop": None,
                "system_message": "system",
                "grounded": False,
                "grounding_text": None,
            }
            out = utils.groq_generate(request, client)
            print(f"Output: {out}")
            assert out == "response text"
            self.print_result("groq_generate", True)
        except Exception:
            self.print_result("groq_generate", False)
            raise


if __name__ == "__main__":
    unittest.main()
