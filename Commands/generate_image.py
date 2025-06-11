from Utils.utils import (
     fetch_cmd_data,
     proxy_request,
     gemini_generate_image,
     GEMINI_IMAGE_MODEL,
     upload_to_kappa,
     check_cooldown,
     download_bytes,
     is_url,
     log_err
)

def reply_with_generate(self, message):
    cmd = fetch_cmd_data(self, message, split_params=True)

    if not check_cooldown(cmd.state, cmd.nick, cmd.cooldown):
        return

    params = cmd.params
    if not params:
        self.send_privmsg(
            cmd.channel,
            f"{cmd.username}, please provide a prompt to generate an image, or use <image_link> <prompt> to edit an existing one, Gemini model: {GEMINI_IMAGE_MODEL}"
        )
        return

    try:
        input_image_b64 = None
        img_url = None
        is_edit = False

        if is_url(params[0]):
            res = proxy_request("GET", params[0])
            mime_type = res.headers.get("Content-Type", "")
            if mime_type and mime_type.startswith('image/'):
                is_edit = True
                img_url = params.pop(0)

        prompt = ' '.join(params)
        if not prompt:
            self.send_privmsg(cmd.channel, f"{cmd.username}, Empty prompt <image_link> <prompt>.")
            return
    
        if is_edit:
            input_image_b64 = download_bytes(img_url)
            if not input_image_b64:
                self.send_privmsg(cmd.channel, f"{cmd.username}, Invalid image URL provided.")
                return

        image_path = gemini_generate_image(prompt, input_image_b64)
        if not image_path:
            self.send_privmsg(cmd.channel, f"{cmd.username}, Image generation failed.")
            return
        
        result_url = upload_to_kappa(image_path, "png", delete_file=True)
        
        if not result_url:
            self.send_privmsg(cmd.channel, f"{cmd.username}, Kappa upload failed.")
            return
        
        prefix = "Edited Image: " if is_edit else ""
        self.send_privmsg(cmd.channel, f"{cmd.username}, {prefix}{result_url}")
        
    except Exception as e:
        self.send_privmsg(cmd.channel, f"{cmd.username}, Unexpected Error occurred; Image generation failed")
        log_err(e)
