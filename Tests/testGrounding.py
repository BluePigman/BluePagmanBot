from Commands.gemini3 import MODEL_NAME, GENERATION_CONFIG, MAX_SOURCES
from Utils.utils import gemini_generate, resolve_redirect_url

def test_search(prompt):
    print("Prompt:", prompt)
    try :
        text, raw_sources = gemini_generate(prompt, MODEL_NAME, GENERATION_CONFIG,  search_grounding=True, return_sources=True)

        if not text:
            print("Text returned as empty.")
            return

        print("Answer:",text)
        if raw_sources:
            sources = []
            for uri in raw_sources[:MAX_SOURCES]:
                resolved = resolve_redirect_url(uri)
                if resolved:
                    sources.append(resolved)
                    break

            if sources:
                print(f"📝 Source(s): {' | '.join(sources)}")
    except Exception as e:
        print(e)

if __name__ == "__main__":
    test_search("What is the current price of the NASDAQ?")