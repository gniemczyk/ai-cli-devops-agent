#!/usr/bin/env python3
"""Zarządzanie konwersacją i historią wiadomości."""

from skills.skills import get_system_prompt_addon
from utils.compact import compress_if_needed, count_messages_tokens
from config import MEMORY_SOFT_LIMIT, MEMORY_WINDOW_LIMIT


class Conversation:
    """Klasa zarządzająca konwersacją z agentem."""
    
    def __init__(self, client):
        self.client = client
        self.messages = self._initialize_messages()
        self.system_message = self.messages[0]
    
    def _initialize_messages(self):
        """Inicjalizuje messages z system prompt."""
        base_prompt = """Jesteś asystentem DevOps o potężnych możliwościach. ODPOWIADAJ ZWIĘŹLE I BEZPOŚREDNIO - nie generuj wewnętrznych monologów ani łańcuchów rozumowania. Jeśli chcesz pozyskać informacje o systemie operacyjnym (np. uruchomić 'docker ps', 'ps aux', 'ls -la'), wygeneruj komendę ujętą dokładnie w specjalne tagi XML: <execute>TWOJA_KOMENDA</execute>.

Użytkownik zostanie natychmiast zapytany o interaktywną zgodę na jej wykonanie. Gdy wyrazi zgodę, komenda zostaje wykonana ukradkiem w tle, a TY zaraz potem otrzymasz od systemu wynik tekstowy tej komendy - wtedy dokonasz dogłębnej analizy dla użytkownika! Wydawaj maksymalnie jedną komendę w okienku."""
        
        skills_prompt = get_system_prompt_addon()
        
        return [
            {"role": "system", "content": base_prompt + "\n" + skills_prompt}
        ]
    
    def add_user_message(self, content):
        """Dodaje wiadomość użytkownika do historii."""
        self.messages.append({"role": "user", "content": content})
    
    def add_assistant_message(self, content):
        """Dodaje odpowiedź asystenta do historii."""
        self.messages.append({"role": "assistant", "content": content})
    
    def clear(self):
        """Czyści historię konwersacji."""
        self.messages = [self.system_message]
    
    def compress(self, threshold=None):
        """Kompresuje historię jeśli przekroczono próg."""
        if threshold is None:
            threshold = MEMORY_SOFT_LIMIT
        
        self.messages = compress_if_needed(
            self.messages,
            threshold,
            MEMORY_WINDOW_LIMIT,
            client=self.client,
            verbose=True
        )
    
    def get_token_count(self):
        """Zwraca liczbę tokenów w obecnej historii."""
        return count_messages_tokens(self.messages)
    
    def get_messages(self):
        """Zwraca kopię obecnych wiadomości."""
        return self.messages.copy()
    
    def remove_last_message(self):
        """Usuwa ostatnią wiadomość z historii."""
        if self.messages:
            self.messages.pop()
