import io
import time
import requests
import mimetypes
from google import genai
from google.genai import types
from config import GOOGLE_API_KEY

def generate():
    client = genai.Client(api_key=GOOGLE_API_KEY)

    model = "gemini-2.0-flash-exp-image-generation"
    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text="beautiful image of night skyline in Toronto")],
        )
    ]
    generate_content_config = types.GenerateContentConfig(
        temperature=1,
        top_p=0.95,
        top_k=40,
        max_output_tokens=8192,
        response_modalities=["image", "text"],
        safety_settings=[
            types.SafetySetting(category="HARM_CATEGORY_CIVIC_INTEGRITY", threshold="OFF")
        ],
        response_mime_type="text/plain",
    )
    try:
        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=generate_content_config,
        )

        result = response.candidates
        if not result:
            return "NONE"
        
        inline_data = result[0].content.parts[0].inline_data
        print(f"Type of data: {type(inline_data.data)}")
        file_extension = mimetypes.guess_extension(inline_data.mime_type) or ".png"
        print(f"Detected file extension: {file_extension}")

        file_data = io.BytesIO(inline_data.data)  # Convert bytes to file-like object
        files = {
            'file': ('generated_image' + file_extension, file_data, inline_data.mime_type)
        }

        # 🔥 Log request details
        with requests.Session() as session:
            request = requests.Request("POST", "https://kappa.lol/api/upload", files=files)
            prepared = session.prepare_request(request)
            
            print("\n🔹 Request Headers:")
            print(prepared.headers)

            print("\n🔹 Request Body (First 500 bytes):")
            print(prepared.body[:500] if prepared.body else "No Body")

            response = session.send(prepared)  # Actually send the request

        time.sleep(1)
        response_json = response.json()
        print("\n🔹 Response:")
        print(response_json)
        print(f"Image Link: {response_json.get('link')}")
        print(f"Delete Link: {response_json.get('delete')}")
        
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    generate()
