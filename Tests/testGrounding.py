from Commands.gemini3 import get_grounding_data, generate

def test_search(prompt):
    grounding_data = get_grounding_data(prompt)
    body_content = grounding_data['body_content']
    duck_urls = grounding_data['duck_urls']

    result = generate(prompt, grounding_text=body_content)
    prefix = "🔎 Grounded: " if body_content else "Not Grounded: "

    for i, m in enumerate(result):
        if i == 0:
            m = prefix + m
        if i == len(result) - 1 and duck_urls:
            m += f" 📝 Source(s): {' | '.join(duck_urls)}"
        print(m)

if __name__ == "__main__":
    test_search("Who is the current pope?")