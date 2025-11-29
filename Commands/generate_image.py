from Utils.utils import (
    fetch_cmd_data,
    SingleWord,
    DEFAULT_UPLOADER,
    proxy_request,
    gemini_generate_image,
    GEMINI_IMAGE_MODEL,
    upload_file,
    check_cooldown,
    download_bytes,
    is_url,
    log_err,
    send_chunks
)

def reply_with_generate(self, message):
    arg_types = {
        ('temperature', 't'): float,
        ('uploader', 'u'): SingleWord
    }
    cmd = fetch_cmd_data(self, message, split_params=True, arg_types=arg_types)

    if not check_cooldown(cmd.state, cmd.nick, cmd.cooldown):
        return

    params = cmd.params
    args = cmd.args
    print(args)

    if not params:
        self.send_privmsg(
            cmd.channel,
            f"{cmd.username}, Please provide a prompt to generate an image, or use image links in the prompt to edit them, Gemini model: {GEMINI_IMAGE_MODEL}"
        )
        return

    try:
        input_images_b64 = []
        url_map = {}
        prompt_parts = []

        for param in params:
            if not is_url(param):
                prompt_parts.append(param)
                continue

            res = proxy_request("GET", param)
            if not res.headers.get("Content-Type", "").startswith('image/'):
                prompt_parts.append(param)
                continue

            img_bytes = download_bytes(param)
            if not img_bytes:
                prompt_parts.append(param)
                continue

            input_images_b64.append(img_bytes)
            url_map[param] = f"(image {len(input_images_b64)})"
            prompt_parts.append(url_map[param])

        prompt = ' '.join(prompt_parts).strip()

        try:
            temperature = args.get("temperature", 1)
            temperature = max(0, min(temperature, 2))
        except Exception:
            temperature = 1
            
        image_path, is_image = gemini_generate_image(
            prompt,
            input_images_b64 if input_images_b64 else None,
            temperature=temperature
        )
        
        if not image_path:
            self.send_privmsg(cmd.channel, f"{cmd.username}, Image generation failed.")
            return

        if not is_image:
            send_chunks(self.send_privmsg, cmd.channel, image_path)
            return

        upload_service = args.get("uploader", DEFAULT_UPLOADER)
        result = upload_file(upload_service, image_path, "png", delete_file=True)
        
        if not result["success"]:
            self.send_privmsg(cmd.channel, f"{cmd.username}, {result['message']}")
            return

        prefix = "Edited image: " if input_images_b64 else ""
        self.send_privmsg(cmd.channel, f"{cmd.username}, {prefix}{result['message']}")

    except Exception as e:
        self.send_privmsg(cmd.channel, f"{cmd.username}, Unexpected Error occurred; Image generation failed")
        log_err(e)
