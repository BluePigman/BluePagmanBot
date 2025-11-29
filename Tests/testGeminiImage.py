from Utils.utils import gemini_generate_image, upload_file

def generate():
    print("Generating image...")
    prompt = "beautiful image of night skyline in Toronto"
    
    result, is_image = gemini_generate_image(prompt)
    
    if not result:
        print("Generation failed completely (None returned).")
        return

    if not is_image:
        print(f"Generation failed to produce image. Text response:\n{result}")
        return

    print(f"Image generated at: {result}")
    
    print("Uploading image...")
    upload_result = upload_file("kappa.lol", result, "png", delete_file=True)
    
    if upload_result["success"]:
        print(f"Upload successful: {upload_result['message']}")
        data = upload_result.get("data")
        if isinstance(data, dict):
            print(f"Delete Link: {data.get('delete')}")
    else:
        print(f"Upload failed: {upload_result['message']}")

if __name__ == "__main__":
    generate()
