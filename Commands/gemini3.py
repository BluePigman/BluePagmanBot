from Utils.utils import (
    send_chunks,
    fetch_cmd_data,
    gemini_generate,
    check_cooldown,
    clean_str,
    resolve_redirect_url,
    log_err
)

MODEL_NAME = "gemini-2.5-flash-lite"
GENERATION_CONFIG = {
    "max_output_tokens": 400,
    "temperature": 0.3,
    "top_p": 0.95,
    "system_instruction": "Please provide a short, concise response with enough detail. Do not use LaTeX or Markdown formatting in your response. Do not ask the user follow up questions, because you are intended to provide a single response with no history and are not expected any follow up prompts. Answer should be at most 600 characters."
}
MAX_SOURCES = 2

def reply_with_grounded_gemini(self, message):
    cmd = fetch_cmd_data(self, message)

    if not check_cooldown(cmd.state, cmd.nick, cmd.cooldown):
        return

    if not cmd.params:
        m = (
            f"{cmd.username}, please provide a prompt for Gemini. "
            f"Model: {MODEL_NAME}, temperature: {GENERATION_CONFIG['temperature']}, "
            f"top_p: {GENERATION_CONFIG['top_p']}"
        )
        self.send_privmsg(cmd.channel, m)
        return

    prompt = cmd.params.strip()

    try:
        text, raw_sources = gemini_generate(prompt, MODEL_NAME, GENERATION_CONFIG, search_grounding=True, return_sources=True)
        if not text:
            self.send_privmsg(cmd.channel, "Failed to generate a response. Please try again later.")
            return

        clean_result = clean_str(text, ['`', '*'])
        send_chunks(self.send_privmsg, cmd.channel, clean_result)

        if raw_sources:
            sources = []
            for uri in raw_sources:
                resolved = resolve_redirect_url(uri)
                if resolved:
                    sources.append(resolved)
                if len(sources) >= MAX_SOURCES:
                    break

            if sources:
                self.send_privmsg(cmd.channel, f"📝 Source(s): {' | '.join(sources)}")

    except Exception as e:
        log_err(e)
        self.send_privmsg(cmd.channel, "Failed to send a response. Please try again later.")
        return
