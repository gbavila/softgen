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
        def __init__(self, client, assistant_id=None):
            self.client = client
            # Opção para usar assistant já existente
            if assistant_id is not None:
                self.assistant_id = assistant_id

        def create(self, name, instructions, model="gpt-3.5-turbo-0125", **kwargs):
            self.assistant = self.client.beta.assistants.create(
                name=name,
                instructions=instructions,
                model=model,
                **kwargs
                )
            self.assistant_id = self.assistant.id
            print(f"Assistant ID: {self.assistant.id}")
                
        def send_message(self, prompt, instructions=None, thread_id=None, **kwargs):
            if (not hasattr(self, 'thread_id') or self.thread_id is None) and thread_id is None:
                self.thread = self.client.beta.threads.create()
                self.thread_id = self.thread.id
                print(f"Thread criada: id = {self.thread.id}")
            else:
                if thread_id is not None:
                    self.thread_id = thread_id
                print(f"Thread existente utilizada: {self.thread_id}")

            message = self.client.beta.threads.messages.create(
                    thread_id=self.thread_id,
                    role="user",
                    content=prompt
                )
            
            self.current_run = self.client.beta.threads.runs.create(
                    thread_id=self.thread_id,
                    assistant_id=self.assistant_id,
                    #instructions=instructions#"Please address the user as Jane Doe. The user has a premium account."
                )
        
        def run_status(self):
            if self.current_run.status == 'completed': 
                messages = self.client.beta.threads.messages.list(
                    thread_id=self.thread_id
                )
                print(messages)
            else:
                print(self.current_run.status)

        def wait_for_run_completion(self, sleep_interval=5):
            while True:
                try:
                    self.current_run = self.client.beta.threads.runs.retrieve(thread_id=self.thread_id, run_id=self.current_run.id)
                    if self.current_run.completed_at:
                        elapsed_time = self.current_run.completed_at - self.current_run.created_at
                        formatted_elapsed_time = time.strftime("%H:%M:%S", time.gmtime(elapsed_time))
                        print(f"Run completed in {formatted_elapsed_time}")
                        messages = self.client.beta.threads.messages.list(thread_id=self.thread_id)
                        return messages
                        # last_message = messages.data[0]
                        # response = last_message.content[0].text.value
                        # print(f"Assistant Response: {response}")
                        # return response
                except Exception as e:
                    raise Exception(f"An error occurred while retrieving the run: {e}")
                print("Waiting for run to complete...")
                time.sleep(sleep_interval)
        
        def get_thread_id(self):
            if hasattr(self, 'thread_id'):
                return self.thread_id
            else:
                return None
    
        def get_assistant_id(self):
            if hasattr(self, 'assistant_id'):
                return self.assistant_id
            else:
                return None

    def assistant(self, assistant_id=None):
        return OpenAIClient.Assistant(self.client, assistant_id)
    
openai_client = OpenAIClient()
