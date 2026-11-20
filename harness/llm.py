import time

import openai
from openai import OpenAI

from . import config

_client = OpenAI(api_key=config.API_KEY, base_url=config.BASE_URL)


def call_model(messages, tool_schemas):
    """One model call, retrying with a growing wait when rate limited."""
    for attempt in range(4):
        try:
            return _client.chat.completions.create(
                model=config.MODEL,
                messages=messages,
                tools=tool_schemas,
                extra_body={"reasoning_effort": config.REASONING_EFFORT},
            )
        except openai.RateLimitError:
            wait = 20 * (attempt + 1)
            print(f"  rate limited, waiting {wait}s...")
            time.sleep(wait)
    raise RuntimeError("still rate limited after retries")