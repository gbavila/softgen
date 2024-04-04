import openai
from django.conf import settings

class OpenAIClient:
    def __init__(self):
        openai.api_key = settings.OPENAI_API_KEY

    def generate_text(self, prompt, model="gpt-3.5-turbo-0125", **kwargs):
        response = openai.chat.completions.create(
             messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model=model,
            **kwargs
        )
        return response.choices[0].message.content.strip()

openai_client = OpenAIClient()