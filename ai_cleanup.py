import os

_client = None

_SYSTEM_PROMPT = (
    "You are a text normalizer for text-to-speech output. "
    "Clean the following extracted document text by: "
    "removing page numbers, headers, and footers; "
    "fixing hyphenated line breaks (re-join words split across lines); "
    "normalizing whitespace (collapse multiple spaces/newlines into single spaces); "
    "removing artifact characters from PDF extraction; "
    "preserving paragraph breaks as single newlines. "
    "Return only the cleaned text with no commentary."
)


def _get_client():
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return None
        from openai import OpenAI
        _client = OpenAI(api_key=api_key)
    return _client


def is_available():
    return bool(os.getenv("OPENAI_API_KEY"))


def clean_text(raw_text):
    """Remove extraction artifacts and normalize text for TTS.
    Falls back to raw_text if OpenAI is unavailable or the call fails."""
    client = _get_client()
    if client is None:
        return raw_text
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": raw_text[:50000]},
            ],
            temperature=0.0,
            max_tokens=16000,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return raw_text
