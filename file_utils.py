import os
import re

def process_file_mentions(text):
    pattern = r'@([^\s]+)'
    paths = set(re.findall(pattern, text))
    
    appended_content = ""
    for path in paths:
        expanded_path = os.path.expanduser(path)
        try:
            if os.path.isfile(expanded_path):
                with open(expanded_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                appended_content += f"\n\n--- Zawartość pliku: {path} ---\n{content}\n-----------------------------------\n"
            else:
                appended_content += f"\n\n[System: Brak pliku {path} lub to nie jest plik]\n"
        except Exception as e:
            appended_content += f"\n\n[System: Błąd wczytywania pliku {path}: {e}]\n"
            
    if appended_content:
        return text + appended_content
    return text
