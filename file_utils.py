import os
import re

def is_safe_path(path):
    """Sprawdza czy ścieżka jest bezpieczna (brak path traversal)."""
    # Konwertuj na ścieżkę bezwzględną
    expanded_path = os.path.expanduser(path)
    abs_path = os.path.abspath(expanded_path)
    
    # Sprawdź czy ścieżka nie zawiera niebezpiecznych sekwencji
    dangerous_patterns = [
        '..',  # parent directory
        '~/',  # home directory (poza kontrolą)
        '/etc/',  # systemowe
        '/usr/',  # systemowe
        '/bin/',  # systemowe
        '/sbin/',  # systemowe
        '/var/',  # systemowe
        '/proc/',  # systemowe
        '/sys/',  # systemowe
        '/dev/',  # systemowe
    ]
    
    path_str = str(abs_path)
    for pattern in dangerous_patterns:
        if pattern in path_str:
            return False
    
    # Sprawdź czy plik istnieje i jest w bieżącym katalogu lub podkatalogach
    current_dir = os.path.abspath(os.getcwd())
    try:
        # Sprawdź czy ścieżka jest w bieżącym katalogu lub jego podkatalogach
        os.path.relpath(abs_path, current_dir)
        return True
    except ValueError:
        # Ścieżka na innym dysku/systemie plików
        return False

def process_file_mentions(text):
    pattern = r'@([^\s]+)'
    paths = set(re.findall(pattern, text))
    
    appended_content = ""
    for path in paths:
        expanded_path = os.path.expanduser(path)
        try:
            # Walidacja bezpieczeństwa ścieżki
            if not is_safe_path(path):
                appended_content += f"\n\n[System: Odrzucono niebezpieczną ścieżkę {path} - ograniczenie bezpieczeństwa]\n"
                continue
                
            if os.path.isfile(expanded_path):
                # Sprawdź rozmiar pliku (ograniczmy do 1MB)
                file_size = os.path.getsize(expanded_path)
                if file_size > 1024 * 1024:  # 1MB
                    appended_content += f"\n\n[System: Plik {path} jest zbyt duży ({file_size} bytes). Maksymalny rozmiar to 1MB]\n"
                    continue
                    
                with open(expanded_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                appended_content += f"\n\n--- Zawartość pliku: {path} ({file_size} bytes) ---\n{content}\n-----------------------------------\n"
            else:
                appended_content += f"\n\n[System: Brak pliku {path} lub to nie jest plik]\n"
        except Exception as e:
            appended_content += f"\n\n[System: Błąd wczytywania pliku {path}: {e}]\n"
            
    if appended_content:
        return text + appended_content
    return text
