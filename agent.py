import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.environ["GROQ_API_KEY"],
    base_url="https://api.groq.com/openai/v1",
)
MODEL = os.environ.get("MODEL", "openai/gpt-oss-120b")

# The conversation history. The model has no memory, so we resend this every call.
messages = [
    {"role": "system", "content": "You are a careful code reviewer. Be concise."},
    {"role": "user", "content": "In two sentences, what is an off-by-one error?"},
]

response = client.chat.completions.create(
    model=MODEL,
    messages=messages,
    extra_body={"reasoning_effort": "low"},  # keeps reasoning tokens down
)

print(response.choices[0].message.content)
print("\n--- usage ---")
print(response.usage)