import config
import google.generativeai as genai
from Commands.describe import generate_gemini_description, get_content_type, upload_file_gemini


def testDescribe(url):
    try:
        media_url = url
        content_type = get_content_type(media_url)
        print("Content type: ", content_type)

        image_file = upload_file_gemini(media_url, content_type)
        
        input_text = "Give me a concise description of this image/gif, ideally under 100 words, translating to English if needed."
        print("Getting description...")
        description = generate_gemini_description(image_file, input_text)
        print(description)

    except Exception as e:
        print(f"Error: {e}")
        return


if __name__ == "__main__":

    testDescribe("https://cdn.7tv.app/emote/01HBKZWPS8000ECTPKPBM8A7MH/4x.webp") # test image
    testDescribe("https://kappa.lol/EHwzUG") # test video
    testDescribe("https://www.adobe.com/support/products/enterprise/knowledgecenter/media/c4611_sample_explain.pdf") # test pdf