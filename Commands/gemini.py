import time
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import config
genai.configure(api_key=config.GOOGLE_API_KEY)

def reply_with_gemini(self, message):
    """
    Handles generating and sending Gemini AI responses to a chat message.
    
    Manages user cooldown and AI response generation for a chat command. If the user is not on cooldown or their last request was sufficiently long ago, it processes their prompt and sends AI-generated responses to the channel.
    
    Parameters:
        self (object): The instance of the chat bot handling the interaction
        message (dict): A dictionary containing message metadata including user, channel, and command details
    
    Behavior:
        - Checks and updates user cooldown state
        - Validates presence of a prompt
        - Generates AI responses using the `generate` function
        - Sends generated responses to the channel with a 1-second delay between messages
    
    Raises:
        No explicit exceptions, but may indirectly raise exceptions during AI response generation
    """
    if (message['source']['nick'] not in self.state or time.time() - self.state[message['source']['nick']] >
            self.cooldown):
        self.state[message['source']['nick']] = time.time()

    if not message['command']['botCommandParams']:
        m = f"@{message['tags']['display-name']}, please provide a prompt for Gemini. Model: gemini-2.0-flash-exp, \
            temperature: 1.1, top_p: 0.95"
        self.send_privmsg(message['command']['channel'], m)
        return

    prompt = (message['command']['botCommandParams'])
    result = generate(prompt)
    for m in result:
        self.send_privmsg(message['command']['channel'], m)
        time.sleep(1)


generation_config = {
    "max_output_tokens": 400,
    "temperature": 1.1,
    "top_p": 0.95,
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
    Generate content from a given prompt using the configured generative AI model.
    
    Generates a response from the AI model, formats the text by replacing newlines and asterisks, 
    and splits the response into chunks of 495 characters.
    
    Parameters:
        prompt (str or list[str]): Input text or list of texts to generate content from
    
    Returns:
        list[str]: A list of response text chunks, each 495 characters or less
    
    Raises:
        Exception: If content generation fails, returns a list with an error message
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


def generate_emote_description(prompt):
    """
    Generate a concise description for a given prompt using the Gemini AI model.
    
    Generates a description without introductory phrases, focusing on direct content generation. Handles potential errors during content generation.
    
    Args:
        prompt (str): The input text for which a description is to be generated.
    
    Returns:
        str or None: A formatted description of the prompt, or None if generation fails.
    
    Raises:
        Exception: Prints and suppresses any errors during content generation.
    """
    system_instruction = [
        "You don't need to say Here's a description, just say the result."]
    try:
        model = genai.GenerativeModel(
            "gemini-2.0-flash-exp",
            system_instruction=system_instruction
        )
        response = model.generate_content(
            prompt,
            generation_config=generation_config,
            safety_settings=safety_settings,
            stream=False,
        ).text.replace('\n', ' ')
        response = response.replace('*', ' ')
        return response
    except Exception as e:
        print(e)
        return None
