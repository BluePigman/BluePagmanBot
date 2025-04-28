import requests
import mimetypes
from google import genai
from google.genai import types
import base64
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
        response_modalities=["image", "text"],
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
        image_bytes = base64.b64decode(inline_data.data) if inline_data.data.startswith(b'iVBORw') else inline_data.data
        
        file_extension = mimetypes.guess_extension(inline_data.mime_type) or ".png"
        files = {
            'file': ('generated_image' + file_extension, image_bytes, inline_data.mime_type)
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
