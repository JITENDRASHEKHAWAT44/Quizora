"""
Thin wrapper around the raw `groq` Python client.

Why this exists:
  llama_index.llms.groq → llama_index.llms.openai → tiktoken
  tiktoken's native DLL (_tiktoken) is blocked by Windows Application Control policies.
  The raw `groq` package has NO dependency on tiktoken and works fine.
"""
import os
from dotenv import load_dotenv

load_dotenv()

_client = None


def _get_client():
    global _client
    if _client is None:
        from groq import Groq
        _client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    return _client


MODEL = "openai/gpt-oss-120b"


class _FakeResponse:
    """Mimics llama_index CompletionResponse so existing code still works."""
    def __init__(self, text: str):
        self.text = text


def groq_complete(prompt: str, model: str = MODEL) -> _FakeResponse:
    """
    Call the Groq chat-completion API and return an object with a .text attribute,
    matching the interface of llama_index's llm.complete() return value.
    """
    client = _get_client()
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    text = response.choices[0].message.content or ""
    return _FakeResponse(text)
