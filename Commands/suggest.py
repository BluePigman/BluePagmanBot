import time, requests, config

def reply_with_suggest(self, message):
        if (message['source']['nick'] not in self.state or time.time() - self.state[message['source']['nick']] >
                self.cooldown):
            self.state[message['source']['nick']] = time.time()
            
            headers = {
            'Authorization': f"Bearer {config.githubToken}",
            'Accept': 'application/vnd.github.v3+json'
             }
            
            body = {
                  'title': message['command']['botCommandParams'] if message['command']['botCommandParams']  else "No Title",
                  'body': f"Suggestion from {message['tags']['display-name']} in #{message['command']['channel']}"
            }

            response = requests.post('https://api.github.com/repos/BluePigman/BluePagmanBot/issues', headers=headers, json=body)
            
            if response.status_code == 201:
                  # created
                response = response.json()
                self.send_privmsg(message['command']['channel'], f"Suggestion created successfully under issue #{response['number']}: \
                {response['html_url']}")
                return

            if response.status_code == 400:
                # bad request
                self.send_privmsg(message['command']['channel'], f"Error {response.status_code}:Bad request.")
                return

            if response.status_code == 403:
                # forbidden
                self.send_privmsg(message['command']['channel'], f"Error {response.status_code}:Forbidden.")
                return
            else:
                self.send_privmsg(message['command']['channel'], f"Error {response.status_code}.")