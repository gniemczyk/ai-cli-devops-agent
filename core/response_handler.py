#!/usr/bin/env python3
"""Obsługa odpowiedzi od API."""

import json
from ui.ui import Colors, print_error
from config import MEMORY_SOFT_LIMIT
from executor.executor_runner import handle_agent_commands


class ResponseHandler:
    """Klasa obsługująca odpowiedzi od API."""
    
    def __init__(self, conversation, client):
        self.conversation = conversation
        self.client = client
    
    def handle_response(self, response):
        """Obsługuje odpowiedź od API.
        
        Zwraca (success, auto_prompt) gdzie:
        - success: czy odpowiedź została poprawnie obsłużona
        - auto_prompt: prompt do automatycznego wysłania (np. po komendzie execute)
        """
        if "error" in response:
            print_error(response["error"])
            self.conversation.remove_last_message()
            return False, None
        
        if "choices" not in response or len(response["choices"]) == 0:
            print_error(f"Dziwny format odpowiedzi z serwera:\n{json.dumps(response, indent=2)}")
            return False, None
        
        agent_reply = response["choices"][0]["message"].get("content")
        
        if agent_reply is None:
            finish_reason = response["choices"][0].get("finish_reason", "brak")
            print_error(f"Otrzymano pustą odpowiedź od API (content = null, finish_reason: {finish_reason}).")
            print(f"{Colors.YELLOW}Diagnostyka - pełna odpowiedź:{Colors.ENDC}")
            print(json.dumps(response, indent=2)[:500] + "..." if len(json.dumps(response)) > 500 else json.dumps(response, indent=2))
            self.conversation.remove_last_message()
            return False, None
        
        # Wyświetl odpowiedź
        tokens_count = response.get("_total_tokens", 0)
        token_info = f" ({tokens_count}t)" if tokens_count > 0 else ""
        print(f"{Colors.GREEN}{Colors.BOLD}🤖 Agent{token_info}:{Colors.ENDC}\n{agent_reply}\n")
        
        # Ostrzeżenie o dużej pamięci
        if tokens_count > MEMORY_SOFT_LIMIT:
            print(f"{Colors.YELLOW}⚠️  Pamięć agenta jest duża ({tokens_count} tokenów). Rozważ wyczyszczenie pamięci poleceniem @clear lub zresetowanie sesji (Ctrl+C i ponowne uruchomienie), aby uniknąć błędów lub wysokich kosztów.{Colors.ENDC}\n")
        
        # Dodaj odpowiedź do historii
        self.conversation.add_assistant_message(agent_reply)
        
        # Obsługa komend <execute>
        next_auto_prompt, executed_something = handle_agent_commands(
            agent_reply, 
            self.conversation.get_messages(), 
            self.client
        )
        
        return True, next_auto_prompt if executed_something else None
