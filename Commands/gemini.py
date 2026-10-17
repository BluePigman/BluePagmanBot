from Utils.utils import (
    fetch_cmd_data,
    check_cooldown,
    clean_str,
    send_chunks,
    gemini_generate,
    log_err
)

MODEL_NAME = "gemini-flash-lite-latest"
GENERATION_CONFIG = {
    "max_output_tokens": 400,
    "system_instruction": (
        "Please always provide a short and concise response. Do not ask the user follow up questions, "
        "because you are intended to provide a single response with no history and are not expected "
        "any follow up prompts. Answer should be at most 990 characters."
    )
}


def reply_with_gemini(self, message):
    cmd = fetch_cmd_data(self, message)

    if not check_cooldown(cmd.state, cmd.nick, cmd.cooldown):
        return

    if not cmd.params:
        m = f"{cmd.username}, please provide a prompt for Gemini. Model: {MODEL_NAME}"
        self.send_privmsg(cmd.channel, m)
        return

    prompt = cmd.params.strip()
    try:
        response = gemini_generate(prompt, MODEL_NAME, GENERATION_CONFIG)
        if not response:
            self.send_privmsg(cmd.channel, f"{cmd.username}, failed to generate a response. Please try again later.")
            return

        clean_result = clean_str(response, ['`', '*'])
        send_chunks(self.send_privmsg, cmd.channel, clean_result)
    except Exception as e:
        log_err(e)
        self.send_privmsg(cmd.channel, "Failed to send a response. Please try again later.")
        return


def generate(prompt) -> list[str]:
    try:
        response = gemini_generate(prompt, MODEL_NAME, GENERATION_CONFIG)
        if not response:
            return ["Error: Failed to generate response."]
        clean = clean_str(response, ['*']).replace('\n', ' ')
        n = 495
        return [clean[i:i+n] for i in range(0, len(clean), n)]
    except Exception as e:
        log_err(e)
        return [f"Error: {str(e)}"]


def generate_emote_description(prompt) -> str | None:
    try:
        config = {
            "system_instruction": "You don't need to say Here's a description, just say the result.",
            "max_output_tokens": 400,
        }
        response = gemini_generate(prompt, MODEL_NAME, config)
        if not response:
            return None
        clean = clean_str(response, ['*']).replace('\n', ' ').replace(r'\&', '&')
        return clean
    except Exception as e:
        log_err(e)
        return None
