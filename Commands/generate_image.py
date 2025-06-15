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
    
    cmd = fetch_cmd_data(self, message, split_params=True, with_args=True)
    
    if not check_cooldown(cmd.state, cmd.nick, cmd.cooldown):
        return

    params = cmd.params
    args = cmd.args
    print(args)
    if not params:
        self.send_privmsg(
            cmd.channel,
            f"{cmd.username}, Please provide a prompt to generate an image, or use <image_link(s)> <prompt> to edit using existing image(s), Gemini model: {GEMINI_IMAGE_MODEL}"
        )
        return

    try:
        input_images_b64 = []
        prompt_start_index = 0

        for i, param in enumerate(params):
            if not is_url(param):
                prompt_start_index = i
                break
            prompt_start_index += 1
            res = proxy_request("GET", param)
            if res.headers.get("Content-Type", "").startswith('image/'):
                img_bytes = download_bytes(param)
                if img_bytes:
                    input_images_b64.append(img_bytes)

        prompt = ' '.join(params[prompt_start_index:])
        if not prompt:
            self.send_privmsg(cmd.channel, f"{cmd.username}, Empty prompt after image link(s).")
            return

        try:
            temperature = 1
            temperature = float(args.get("temperature"))
            temperature = max(0, min(temperature, 2))
        except Exception:
            pass

        image_path = gemini_generate_image(
            prompt,
            input_images_b64 if input_images_b64 else None,
            temperature=temperature
        )
        if not image_path:
            self.send_privmsg(cmd.channel, f"{cmd.username}, Image generation failed.")
            return

        result_url = upload_to_kappa(image_path, "png", delete_file=True)
        if not result_url:
            self.send_privmsg(cmd.channel, f"{cmd.username}, Kappa upload failed.")
            return

        prefix = "Edited image: " if input_images_b64 else ""
        self.send_privmsg(cmd.channel, f"{cmd.username}, {prefix}{result_url}")

    except Exception as e:
        self.send_privmsg(cmd.channel, f"{cmd.username}, Unexpected Error occurred; Image generation failed")
        log_err(e)
