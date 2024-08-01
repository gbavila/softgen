import time
from openai import OpenAI
from django.conf import settings
from textwrap import dedent

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
            # Option to use existing assistant
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
                print(f"Thread created: id = {self.thread.id}")
            else:
                if thread_id is not None:
                    self.thread_id = thread_id
                print(f"Using existing Thread: {self.thread_id}")

            self.client.beta.threads.messages.create(
                    thread_id=self.thread_id,
                    role="user",
                    content=prompt
                )
            
            self.current_run = self.client.beta.threads.runs.create(
                    thread_id=self.thread_id,
                    assistant_id=self.assistant_id,
                    instructions=instructions #"Please address the user as Jane Doe. The user has a premium account."
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
        
        def get_thread_messages(self, thread_id):
            messages = self.client.beta.threads.messages.list(thread_id=thread_id)
            return messages
        
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

example_processed_specs = dedent("""
Project: PC Build Cost Calculator

Overview: This project is a simple web page with features for adding pc build components and its prices, calculating the total cost for the build.

Scope: The PC Build Cost Calculator is a single-page web application that does not persist data across sessions. 
        It will run in a single framework and be deployed on the Vercel platform. 
        The application will not require user authentication or additional security measures.

Framework: Django

Product Functions:
1. Display a styled header with the project name.
2. Provide an interactive table for adding and displaying PC components and their prices.
3. Calculate and display the total cost of the build.
4. Color-code table rows based on the component price relative to the total cost.
5. Include a button to copy the table content to the clipboard.

Operating Environment
1. The application will be deployed on the Vercel platform.
2. It should function correctly on modern web browsers (e.g., Chrome, Firefox, Edge, Safari).

Functional Requirements:
1. Web Page Header
- Description: Display a styled header with the project name.
- Inputs: None
- Outputs: Visible header at the top of the page.
- Functionality: The header will be styled to be visually appealing.
2. Interactive Center Table
- Description: Provide an interactive table for adding PC components.
- Inputs: Component name and price entered by the user.
- Outputs: Displayed component list with prices and color-coded rows.
- Functionality: The table will have two columns: component name and price.
    Rows will be auto-colored based on the price:
    Green: Less than 10% of the total cost.
    Yellow: Between 10% and 20% of the total cost.
    Red: More than 20% of the total cost.
3. Copy Table to Clipboard
- Description: Provide a button to copy the table content to the clipboard.
- Inputs: User clicks the copy button.
- Outputs: Table content copied to the clipboard.
- Functionality: A button will be available to copy the entire table content.

Non-Functional Requirements:
1. Security Requirements:
No additional security features required as the page is public and does not involve login.
2. Usability Requirements:
The user interface should be simple and intuitive.
The application should provide clear feedback for user actions (e.g., confirmation message when copying to clipboard).

Routes:
1. root endpoint for the single page: /

Run Environment: Deployment on Vercel platform, project should have all files and structure needed for Vercel to understand and deploy the page when integrating with github repository.

Technical Requirements:
1. Project should have all files and structures needed to be run at Vercel platform.
2. UI must be simple and easy to use.
3. Page should work in most browsers.

""")
# Not adding framework so it wont introduce a bias into the model
