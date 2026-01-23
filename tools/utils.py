from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def call_llm(user_prompt: str, system_prompt: str, model: str = "gpt-4o-mini") -> str:

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.0,
            max_tokens=100
        )
        return response.choices[0].message.content
    except Exception as e:
        raise Exception(f"LLM call failed: {str(e)}")
