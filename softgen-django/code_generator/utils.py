from datetime import datetime
import json
from textwrap import dedent
from .serializers import LLM_Run_StatsSerializer
from .models import Software
from .services.openai import OpenAIClient, example_processed_specs
from django.conf import settings

def process_file_list(list: list):
    filtered_files = []
    for path in list:
        if '.' in path or 'dockerfile' in path.lower():
            parts = path.rsplit('.', 1)
            if len(parts) > 1 and parts[1] or 'dockerfile' in parts[0].lower():
                filtered_files.append(path)
            else:
                print(f'{path} removed from file list.')
        else:
            print(f'{path} removed from file list.')

    return filtered_files

def json_load_message(message):
    try:
        loaded = json.loads(message, strict=True)
    except json.JSONDecodeError:
        print('json.JSONDecodeError, trying to parse with strict=False')
        loaded = json.loads(message, strict=False)
    except:
        raise
    
    return loaded

def filter_assistant_messages(messages):
    return [json_load_message(message.content[0].text.value) for message in messages if message.role == 'assistant']

def check_already_generated(messages) -> dict:
    analysis = {'failed': False, 'generated': [], 'files': []}
    assistant_messages = filter_assistant_messages(messages)
    
    for msg in assistant_messages:
        if msg.get('framework'):
            analysis['framework'] = msg.get('framework')
            analysis['files'] = msg.get('files')
            print(f"LLM's generated list: {analysis['files']}")
        elif msg.get('instructions'):
            analysis['generated'].append(msg)

    # for msg in analysis['generated']:
    #     try:
    #         analysis['files'].remove(msg.get('file'))
    #     except:
    #         pass

    if (len(analysis['generated']) == 0 and len(analysis['files']) == 0):
        analysis['failed'] = True

    # analysis = {'framework': 'Django', 
    #             'failed': False, 
    #             'generated': [{'file': '...', 'instructions': '...', 'content': '...'}, ..., {'file': '...', 'instructions': '...', 'content': '...'}], 
    #             'files': ['file_1', ..., 'file_n']}
    return analysis

def get_latest_openai_messages(messages):
    
    last_user_message_index = None

    for index, message in enumerate(messages):
        if message.role == 'user':
            last_user_message_index = index
            break

    if last_user_message_index is None:
        # No user message found, return an empty list
        return []

    # Collect all messages after the last user message
    #messages_after_last_user = messages[last_user_message_index + 1:]
    messages_after_last_user = messages[0:last_user_message_index]
    return messages_after_last_user

def save_llm_run_stats(
        software_id: int,
        time_start: datetime,
        run_number: int = 1, 
        manual_trigger: bool = False,
        model: str = 'gpt-3.5-turbo-0125'
        ) -> None:
    
    run_stats = {
        'software': software_id,
        'run_number': run_number,
        'manual_trigger': manual_trigger,
        'model': model,
        'time_elapsed': datetime.now() - time_start
        }
    print(f"Run completed in {run_stats['time_elapsed']} s")

    serializer = LLM_Run_StatsSerializer(data=run_stats)
    if serializer.is_valid():
        serializer.save()
    else:
        # Dont want to raise any erros, so run wont be impacted
        print(f'Could not create LLM stats object: {serializer.errors}')

def process_specs(software: Software) -> Software:
    raw_specs = software.specs
    assistant = OpenAIClient().assistant(settings.SPECS_ASSISTANT_ID)

    proc_specs_prompt = dedent(f"""
    Using as example the software requirement specification (SRS) that i will give you, generate a similar SRS for this software request:
    {raw_specs}
    End of request.
    Software requirement specification example:
    {example_processed_specs}
    End of example.
    There is no need to strictly follow the example, but elements you should not modify from the example are:
    - Deployment on vercel platform and everything related to it.
    - Choose a single framework, there should not be any database involved. Change framework if suited.
    """)

    assistant.send_message(
        prompt=proc_specs_prompt
    )
    response = assistant.wait_for_run_completion()
    assistant_messages = filter_assistant_messages(response.data)

    if len(assistant_messages) > 1:
        print('[WARNING] More than 1 message retrieved in specs processing response')
    
    software.processed_specs = assistant_messages[0]['srs']
    software.save()

    return software
