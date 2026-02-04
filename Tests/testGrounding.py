from Commands.gemini3 import get_grounding_data, MODEL_NAME, GENERATION_CONFIG
from Utils.utils import gemini_generate

def test_search(prompt):
    grounding_data = get_grounding_data(prompt)
    if not grounding_data:
        print("No grounding data found.")
        return
        
    body_content = grounding_data.get('body_content')
    duck_urls = grounding_data.get('valid_urls')

    request = {
        "prompt": prompt,
        "grounded": bool(body_content),
        "grounding_text": body_content
    }

    result = gemini_generate(request, MODEL_NAME, GENERATION_CONFIG)
    
    prefix = "🔎 Grounded: " if body_content else "Not Grounded: "
    print(f"{prefix}{result}")
    if duck_urls:
        print(f" 📝 Source(s): {' | '.join(duck_urls)}")

if __name__ == "__main__":
    test_search("Who is the current pope?")