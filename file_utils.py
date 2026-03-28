import os
import re

def is_safe_path(path):
    """Sprawdza czy ścieżka jest bezpieczna (brak path traversal i dostęp tylko do plików projektu)."""
    # Rozwiń ~ i pobierz ścieżkę bezwzględną
    try:
        expanded_path = os.path.expanduser(path)
        abs_path = os.path.abspath(expanded_path)
        current_dir = os.path.abspath(os.getcwd())
        
        # Sprawdź, czy ścieżka nie wychodzi poza bieżący katalog roboczy
        # os.path.commonpath zwróci wspólny prefiks; jeśli nie jest nim current_dir, to ścieżka jest "na zewnątrz"
        common = os.path.commonpath([current_dir, abs_path])
        if common != current_dir:
            return False
            
        # Dodatkowa czarna lista dla bezpieczeństwa (nawet wewnątrz projektu)
        path_str = str(abs_path)
        dangerous_patterns = [
            '.env',      # pliki konfiguracyjne z kluczami
            '.git',      # metadane git
            '__pycache__',
            '.ssh',      # gdyby ktoś wrzucił link symboliczny itp.
        ]
        
        for pattern in dangerous_patterns:
            if pattern in path_str:
                return False
                
        return True
    except Exception:
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
