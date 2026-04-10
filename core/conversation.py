#!/usr/bin/env python3
"""Zarządzanie konwersacją i historią wiadomości."""

from skills.skills import get_system_prompt_addon
from utils.compact import compress_if_needed, count_messages_tokens
from config import MEMORY_SOFT_LIMIT, MEMORY_WINDOW_LIMIT
from core.system_prompt import SYSTEM_PROMPT


class Conversation:
    """Klasa zarządzająca konwersacją z agentem."""
    
    def __init__(self, client):
        self.client = client
        self.messages = self._initialize_messages()
        self.system_message = self.messages[0]
    
    def _initialize_messages(self):
        """Inicjalizuje messages z system prompt."""
        skills_prompt = get_system_prompt_addon()
        
        return [
            {"role": "system", "content": SYSTEM_PROMPT + "\n" + skills_prompt}
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
        
        if threshold < 0:
            raise ValueError(f"Próg kompresji musi być nieujemny, otrzymano: {threshold}")
        
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
