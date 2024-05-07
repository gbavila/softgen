
def process_file_list(list: list):
    filtered_files = []
    for path in list:
        if '.' in path:
            parts = path.rsplit('.', 1)
            if len(parts) > 1 and parts[1]:
                filtered_files.append(path)
            else:
                print(f'{path} removed from file list.')

    return filtered_files