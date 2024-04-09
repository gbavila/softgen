import time
from openai import OpenAI
from django.conf import settings

class OpenAIClient:
    def __init__(self):
        self.client = OpenAI()
        self.client.api_key = settings.OPENAI_API_KEY

    def generate_text(self, prompt, model="gpt-3.5-turbo-0125", **kwargs):
        response = self.client.chat.completions.create(
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
    
    class Assistant:
        def __init__(self, client):
            self.client = client

        def create(self, name, instructions, model="gpt-3.5-turbo-0125", **kwargs):
            self.assistant = self.client.beta.assistants.create(
                name=name,
                instructions=instructions,
                #tools=[{"type": "code_interpreter"}],
                model=model,
                )
                
        def send_message(self, prompt, instructions):
            if not hasattr(self, 'thread') or self.thread is None:
                self.thread = self.client.beta.threads.create()

            message = self.client.beta.threads.messages.create(
                    thread_id=self.thread.id,
                    role="user",
                    content=prompt
                )
            
            self.current_run = self.client.beta.threads.runs.create_and_poll(
                    thread_id=self.thread.id,
                    assistant_id=self.assistant.id,
                    instructions=instructions#"Please address the user as Jane Doe. The user has a premium account."
                )
        
        def run_status(self):
            if self.current_run.status == 'completed': 
                messages = self.client.beta.threads.messages.list(
                    thread_id=self.thread.id
                )
                print(messages)
            else:
                print(self.current_run.status)

        def wait_for_run_completion(self, sleep_interval=5):
            while True:
                try:
                    if self.current_run.completed_at:
                        elapsed_time = self.current_run.completed_at - self.current_run.created_at
                        formatted_elapsed_time = time.strftime("%H:%M:%S", time.gmtime(elapsed_time))
                        print(f"Run completed in {formatted_elapsed_time}")

                        messages = self.client.beta.threads.messages.list(thread_id=self.thread_id)
                        last_message = messages.data[0]
                        response = last_message.content[0].text.value
                        print(f"Assistant Response: {response}")
                        return response
                except Exception as e:
                    raise Exception(f"An error occurred while retrieving the run: {e}")
                print("Waiting for run to complete...")
                time.sleep(sleep_interval)

    def assistant(self):
        return OpenAIClient.Assistant(self.client)
    
openai_client = OpenAIClient()
