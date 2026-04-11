import os
import re

def is_safe_path(path):
    """Sprawdza czy ścieżka jest bezpieczna (brak path traversal i dostęp tylko do plików projektu)."""
    # Rozwiń ~ i pobierz ścieżkę bezwzględną
    try:
        expanded_path = os.path.expanduser(path)
        # os.path.realpath rozwiązuje wszystkie symlinki, os.path.abspath tego nie gwarantuje w 100%
        abs_path = os.path.realpath(expanded_path)
        current_dir = os.path.realpath(os.getcwd())
        
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
    """
    Wyłapuje wzorce @cos_tam. 
    Zwraca (zmodyfikowany_tekst, lista_wykrytych_komend)
    """
    pattern = r'@([^\s]+)'
    found_mentions = re.findall(pattern, text)
    
    # Komendy systemowe, które nie powinny być traktowane jako pliki
    system_commands = ['clear', 'compact']
    
    commands_triggered = []
    clean_text = text
    appended_content = ""
    
    # Najpierw usuwamy komendy z tekstu, żeby nie "straszyły" agenta
    for mention in found_mentions:
        if mention.lower() in system_commands:
            commands_triggered.append(mention.lower())
            # Usuwamy @command z tekstu wysyłanego do LLM
            clean_text = clean_text.replace(f"@{mention}", "").strip()
            continue

        # Jeśli to nie komenda, traktujemy jak plik
        path = mention
        
        # Pomiń ścieżki absolutne systemowe (np. @/dev, @/etc) - to nie są pliki projektu
        if path.startswith('/'):
            continue
            
        # Pomiń path traversal attempts
        if '..' in path:
            appended_content += f"\n\n[System: Odrzucono nieprawidłową ścieżkę {path}]\n"
            continue
            
        expanded_path = os.path.expanduser(path)
        try:
            # Walidacja bezpieczeństwa ścieżki
            if not is_safe_path(path):
                appended_content += f"\n\n[System: Odrzucono niebezpieczną ścieżkę {path} - ograniczenie bezpieczeństwa]\n"
                continue
                
            if os.path.isfile(expanded_path):
                file_size = os.path.getsize(expanded_path)
                if file_size > 1024 * 1024:  # 1MB
                    appended_content += f"\n\n[System: Plik {path} jest zbyt duży ({file_size} bytes). Maksymalny rozmiar to 1MB]\n"
                    continue
                    
                with open(expanded_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                appended_content += f"\n\n--- Zawartość pliku: {path} ({file_size} bytes) ---\n{content}\n-----------------------------------\n"
            else:
                # Jeśli to nie był plik i nie była to komenda, zostawiamy w tekście (może to być np. handle na twitterze w zapytaniu)
                pass
        except Exception as e:
            appended_content += f"\n\n[System: Błąd wczytywania pliku {path}: {e}]\n"
            
    final_text = clean_text
    if appended_content:
        final_text += appended_content
        
    return final_text, commands_triggered
