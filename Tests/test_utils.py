import unittest
import os
import tempfile
from unittest.mock import patch, MagicMock
import gc
import config
from Utils.utils import *

class TestUtilities(unittest.TestCase):

    def print_result(self, test_name, passed, output=""):
        GREEN = "\033[92m"
        RED = "\033[91m"
        RESET = "\033[0m"
        status = f"{GREEN}PASSED{RESET}" if passed else f"{RED}FAILED{RESET}"
        print(f"\n========== Testing {test_name} ==========")
        if output:
            print(output)
        print(status)

    def test_check_cooldown(self):
        state = {}
        nick = "user1"
        cooldown = 1
        result1 = check_cooldown(state, nick, cooldown)
        output1 = f"First call result: {result1}"
        result2 = check_cooldown(state, nick, cooldown)
        output2 = f"Second call result: {result2}"
        passed = result1 is True and result2 is False
        self.print_result("check_cooldown", passed, output1 + "\n" + output2)
        self.assertTrue(passed)

    def test_chunk_str(self):
        text = "word " * 100
        chunks = chunk_str(text, chunk_size=20)
        output = f"Number of chunks: {len(chunks)}\nFirst chunk: {chunks[0]}"
        passed = all(len(chunk) <= 20 for chunk in chunks)
        self.print_result("chunk_str", passed, output)
        self.assertTrue(passed)

    def test_clean_str(self):
        text = "  some   test   string \n "
        cleaned = clean_str(text, remove=["t"])
        output = f"Cleaned string: '{cleaned}'"
        passed = "t" not in cleaned and "  " not in cleaned
        self.print_result("clean_str", passed, output)
        self.assertTrue(passed)

    def test_fetch_cmd_data(self):
        message = {
            'command': {'botCommandParams': 'param1 arg1:val1 arg2:val2', 'channel': '#chan'},
            'tags': {'display-name': 'tester'},
            'source': {'nick': 'nick1'}
        }
        class Dummy:
            state = {"state": 1}
            cooldown = 10
        result = fetch_cmd_data(Dummy(), message, with_args=True)
        output = f"Params: {result.params}, Args: {result.args}, Username: {result.username}"
        passed = (result.params == "param1" and
                  result.args == {'arg1': 'val1', 'arg2': 'val2'} and
                  result.username == "@tester")
        self.print_result("fetch_cmd_data", passed, output)
        self.assertTrue(passed)

    def test_fetch_firefox_cookies(self):
        tmp_db = tempfile.NamedTemporaryFile(delete=False)
        tmp_db.close()
        try:
            with open(tmp_db.name, 'wb') as f:
                f.write(b"")  # placeholder

            config.FIREFOX_COOKIES_PATH = tmp_db.name

            try:
                cookies = fetch_firefox_cookies(as_netscape=False)
                output = f"Cookies dict: {cookies}"
                passed = isinstance(cookies, dict)
            except Exception as e:
                output = str(e)
                passed = False

            self.print_result("fetch_firefox_cookies", passed, output)
            self.assertTrue(passed)
        finally:
            gc.collect()  # force release file handles
            os.unlink(tmp_db.name)

    def test_parse_str(self):
        html = "<html><body>test</body></html>"
        parsed_html = parse_str(html, "html")
        json_str = '{"key":"value"}'
        parsed_json = parse_str(json_str, "json")
        output = f"HTML tag: {parsed_html.body.name}, JSON key: {list(parsed_json.keys())[0]}"
        passed = (parsed_html.body.name == "body" and parsed_json["key"] == "value")
        self.print_result("parse_str", passed, output)
        self.assertTrue(passed)

        with self.assertRaises(ValueError):
            parse_str("data", "invalid")

    def test_send_chunks(self):
        sent = []
        def fake_send(channel, text):
            sent.append(text)

        text = "word " * 50
        send_chunks(fake_send, "#chan", text, chunk_size=20)
        output = f"Chunks sent: {len(sent)}"
        passed = all(len(c) <= 20 for c in sent)
        self.print_result("send_chunks", passed, output)
        self.assertTrue(passed)

    @patch('Utils.utils.proxy_request')
    def test_download_bytes(self, mock_req):
        mock_resp = MagicMock()
        mock_resp.content = b"data"
        mock_resp.raise_for_status = lambda: None
        mock_req.return_value = mock_resp
        data = download_bytes("http://example.com")
        output = f"Downloaded bytes length: {len(data) if data else 'None'}"
        passed = data == b"data"
        self.print_result("download_bytes", passed, output)
        self.assertTrue(passed)

    @patch('Utils.utils.proxy_request')
    def test_upload_to_kappa(self, mock_req):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"link": "http://kappa.lol/upload.png"}
        mock_resp.raise_for_status = lambda: None
        mock_req.return_value = mock_resp
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"test")
            tmp_path = tmp.name

        link = upload_to_kappa(tmp_path, "png")
        output = f"Upload returned link: {link}"
        passed = link == "http://kappa.lol/upload.png"
        self.print_result("upload_to_kappa", passed, output)
        self.assertTrue(passed)

if __name__ == "__main__":
    unittest.main()
