from Commands.describe import generate_gemini_description, get_content_type, upload_file_gemini, gemini_for_video


def testDescribe(url):
    try:
        media_url = url
        content_type = get_content_type(media_url)
        print("Content type:", content_type)
        if not content_type:
            raise RuntimeError("Unable to determine content type")

        if content_type.startswith("image/"):
            media = upload_file_gemini(media_url, content_type)
            input_text = "Give me a concise description of this image/gif, ideally under 100 words, translating to English if needed."
            print("Getting description...")
            description = generate_gemini_description(media, input_text)
        elif content_type.startswith("video/"):
            media = upload_file_gemini(media_url, content_type)
            input_text = "Describe the content of this video, in under 100 words, translating to English if needed."
            print("Getting video description...")
            description = gemini_for_video(media, input_text)
        elif content_type == "application/pdf":
            media = upload_file_gemini(media_url, content_type)
            input_text = "Summarize this pdf, translating to English if needed."
            print("Getting PDF summary...")
            description = generate_gemini_description(media, input_text)
        else:
            raise AssertionError(f"Unhandled content type: {content_type}")

        print(description)

    except Exception as e:
        print(f"Error: {e}")
        return


if __name__ == "__main__":

    testDescribe("https://cdn.7tv.app/emote/01HBKZWPS8000ECTPKPBM8A7MH/4x.webp") # test image
    testDescribe("https://kappa.lol/EHwzUG") # test video
    testDescribe("https://www.adobe.com/support/products/enterprise/knowledgecenter/media/c4611_sample_explain.pdf") # test pdf