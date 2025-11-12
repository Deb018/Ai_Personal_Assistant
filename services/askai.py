"""services.askai

Lightweight wrapper around the Google Generative AI client that exposes an
async-friendly `ask_ai(prompt: str) -> str` function usable from FastAPI.

Behavior and choices:
- API key is read from environment variables: GENAI_API_KEY or GOOGLE_API_KEY.
- The module configures the client lazily at import time if the key exists.
- Retries are implemented in the sync inner worker and executed in a
  threadpool so the event loop is not blocked.
"""

import os
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

import google.generativeai as genai

# Look up the API key from common env var names. Do not hardcode keys.
_API_KEY = "AIzaSyC23lEVS6PFM4AHvU7rsNa0-HNbo06BMv4"
_configured = False
_model = None
if _API_KEY:
    # configure the client; if the package or runtime environment is missing
    # this will raise at import time which is acceptable so failures surface
    # quickly when running the app.
    genai.configure(api_key=_API_KEY)
    _model = genai.GenerativeModel("gemini-2.5-flash")
    _configured = True


def _ask_sync(prompt: str, retries: int = 3, backoff: float = 2.0) -> str:
    """Synchronous helper that calls the genai client with retries.

    Runs in a threadpool when used from async code.
    """
    if not _configured or _model is None:
        raise RuntimeError(
            "Generative AI API key not configured. Set GENAI_API_KEY or GOOGLE_API_KEY environment variable."
        )

    last_exc: Optional[Exception] = None
    for attempt in range(1, retries + 1):
        try:
            # original script used `generate_content(prompt)` and returned `.text`.
            # Keep the same call but defensively access common attributes.
            response = _model.generate_content(prompt)
            text = getattr(response, "text", None) or getattr(response, "content", None)
            if text is None:
                # fallback to string representation
                return str(response)
            return text
        except Exception as e:
            last_exc = e
            # simple exponential-backoff-ish sleep
            time.sleep(backoff)
            backoff *= 1.5

    # If all retries failed, raise the last exception so callers can handle it.
    raise last_exc


async def ask_ai(prompt: str, retries: int = 3, backoff: float = 2.0, executor: Optional[ThreadPoolExecutor] = None) -> str:
    """Async wrapper around the sync client call.

    This function is safe to call from FastAPI endpoints (it won't block the
    event loop because it runs the sync client in a threadpool).
    """
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(executor, _ask_sync, prompt, retries, backoff)


if __name__ == "__main__":
    # Small CLI for local testing; uses asyncio to call the async wrapper.
    print("Starting interactive assistant (Ctrl-C to exit). Make sure GENAI_API_KEY is set.")

    try:
        while True:
            user = input("You: ")
            if user.strip().lower() in {"bye", "exit", "quit"}:
                print("Assistant: Bye!")
                break
            try:
                reply = asyncio.run(ask_ai(user))
            except Exception as e:
                reply = f"Error: {e}"
            print("Assistant:", reply)
    except (KeyboardInterrupt, EOFError):
        print("\nExiting.")