from Commands.summarize import get_transcript, model, SUMMARY_CHAR_LIMIT, TranscriptError, TranscriptUnavailableError
from Utils.utils import gemini_generate, clean_str


def run_test(video_id, description="Video"):
    print(f"\n--- Testing {description} (Video ID: {video_id}) ---")

    try:
        transcript = get_transcript(video_id)
        print(f"Success! Transcript excerpt (first 200 chars): {transcript[:200]}...")
        print(f"Total transcript length: {len(transcript)} characters")

        print("\nGenerating summary...")
        prompt = {
            "prompt": (
                f"Summarize the following YouTube transcript in under {SUMMARY_CHAR_LIMIT} "
                "characters. Ignore sponsor segments and calls to subscribe/like/etc. "
                "Give your summarization in English only."
            ),
            "grounded": True,
            "grounding_text": clean_str(transcript),
        }
        print(transcript)
        #summary = gemini_generate(prompt, model)
        #print(f"\nSummary:\n{summary}")

    except TranscriptUnavailableError as e:
        print(f"Expected failure (No Captions): {e}")
    except TranscriptError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Unexpected Error: {e}")


# Test Case 1: Success
run_test("-wa2JEYl9jU", "Valid Video with Captions")

# Test Case 2: Failure (No Captions)
run_test("DiBmoMOmeck", "Video without Captions")
