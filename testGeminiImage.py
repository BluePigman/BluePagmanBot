import mimetypes
import time
from google import genai
from google.genai import types
import requests
from config import GOOGLE_API_KEY

def generate():
    client = genai.Client(
        api_key=GOOGLE_API_KEY,
    )

    model = "gemini-2.0-flash-exp-image-generation"
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text="""beautiful image of night skyline in toronto    """),
            ],
        )
    ]
    generate_content_config = types.GenerateContentConfig(
        temperature=1,
        top_p=0.95,
        top_k=40,
        max_output_tokens=8192,
        response_modalities=[
            "image",
            "text",
        ],
        safety_settings=[
            types.SafetySetting(
                category="HARM_CATEGORY_CIVIC_INTEGRITY",
                threshold="OFF",  # Off
            ),
        ],
        response_mime_type="text/plain",
    )
    


    for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
    ):
        if not chunk.candidates or not chunk.candidates[0].content or not chunk.candidates[0].content.parts:
            continue
        if chunk.candidates[0].content.parts[0].inline_data:
            file_name = "ENTER_FILE_NAME"
            inline_data = chunk.candidates[0].content.parts[0].inline_data
            file_extension = mimetypes.guess_extension(inline_data.mime_type)
            # save_binary_file(
            #     f"{file_name}{file_extension}", inline_data.data
            # )
            files = {
                'file': inline_data.data # bytestring
            }
            response = requests.post('https://kappa.lol/api/upload',files=files)
            time.sleep(1)
            response = response.json()
            try:
                print(response)
                print(response["link"])
                print(response["delete"])
            except Exception as e:
                print(e)
            # print(
            #     "File of mime type"
            #     f" {inline_data.mime_type} saved"
            #     f"to: {file_name}"
            # )
        else:
            print(chunk.text)

if __name__ == "__main__":
    generate()
