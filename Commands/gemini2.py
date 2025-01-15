import time
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import config
genai.configure(api_key=config.GOOGLE_API_KEY)

def reply_with_gemini_experimental(self, message):
    """
    Generates a response from the Gemini AI model for a user's prompt in a chat environment.
    
    This method handles user interaction with an experimental Gemini AI model, managing cooldown periods and sending AI-generated responses to a chat channel.
    
    Parameters:
        message (dict): A dictionary containing message metadata including:
            - 'source': User information
            - 'tags': User display name
            - 'command': Command details with bot parameters
            - 'command']['channel']: Target chat channel
    
    Behavior:
        - Enforces a cooldown period between user interactions
        - Validates the presence of a user prompt
        - Generates AI responses using the `generate` function
        - Sends AI responses to the chat channel with a 1.5-second delay between messages
    
    Raises:
        No explicit exceptions are raised within the method
    """
    if (message['source']['nick'] not in self.state or time.time() - self.state[message['source']['nick']] >
            self.cooldown):
        self.state[message['source']['nick']] = time.time()

    if not message['command']['botCommandParams']:
        m = f"@{message['tags']['display-name']}, please provide a prompt for Gemini. Model: gemini-2.0-flash-exp, \
            temperature: 2, top_p: 0.75"
        self.send_privmsg(message['command']['channel'], m)
        return

    prompt = message['command']['botCommandParams']
    result = generate(prompt)
    for m in result:
        self.send_privmsg(message['command']['channel'], m)
        time.sleep(1.5)


generation_config = {
    "max_output_tokens": 400,
    "temperature": 2,
    "top_p": 0.75,
}

safety_settings = {
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
}

system_instruction=["""Please always provide a short and concise response. Do not ask the user follow up questions, 
                        because you are intended to provide a single response with no history and are not expected
                        any follow up prompts. If given a media file, please describe it. For GIFS/WEBP files describe all frames.
                        Answer should be at most 990 characters."""]

model = genai.GenerativeModel(
  model_name="gemini-2.0-flash-exp",
  generation_config=generation_config,
  safety_settings=safety_settings,
  system_instruction=system_instruction
)

def generate(prompt) -> list[str]:
    """
    Generate a response from the Gemini AI model by processing the given prompt.
    
    Parameters:
        prompt (str or list[str]): The input text or list of texts to generate a response for.
    
    Returns:
        list[str]: A list of response chunks, each no longer than 495 characters. 
                   If an error occurs, returns a list with an error message.
    
    Raises:
        Handles any exceptions during content generation, printing the error and 
        returning an error message as a list.
    
    Notes:
        - Converts single string prompts to a list
        - Removes newline and asterisk characters from the response
        - Splits long responses into chunks of 495 characters
    """
    try:
        if isinstance(prompt, str):
            prompt = [prompt]
        response = model.generate_content(
            prompt,
            stream=False,
        ).text.replace('\n', ' ')
        response = response.replace('*', ' ')
        n = 495
        return [response[i:i+n] for i in range(0, len(response), n)]
    except Exception as e:
        print(e)
        return ["Error: ", e[0:490]]