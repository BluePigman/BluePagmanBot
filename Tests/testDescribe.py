import os
import requests
import google.generativeai as genai
from Commands.describe import generate_gemini_description, get_content_type

def testDescribe(url):
    media_url = url
    content_type = get_content_type(media_url)
    print("Content type: ", content_type)

    if content_type in ['image/jpeg', 'image/png', 'image/webp', 'image/gif']:
        try:
            # Download the image
            image_response = requests.get(media_url, stream=True)
            
            # Determine file extension from content type
            extension_map = {
                'image/jpeg': 'jpg',
                'image/png': 'png',
                'image/webp': 'webp',
                'image/gif': 'gif'
            }
            extension = extension_map.get(content_type, 'jpg')
            
            # Save image to a temporary file
            image_file_name = f"temp_image.{extension}"
            with open(image_file_name, 'wb') as image_file:
                image_file.write(image_response.content)

            # Upload the saved image to Gemini
            image_file = genai.upload_file(image_file_name, mime_type=content_type)
            
            input_text = "Give me a concise description of this image/gif, ideally under 100 words, translating to English if needed."
            print("Getting description...")
            description = generate_gemini_description(image_file, input_text)

            # Clean up - delete the temporary file
            os.remove(image_file_name)
            
            print(description)

        except Exception as e:
            print(f"Error: {e}")
            return