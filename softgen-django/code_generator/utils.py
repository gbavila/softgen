import json

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
