#!/usr/bin/env python3
"""Obsługa interfejsu wiersza poleceń i komend użytkownika."""

from ui.ui import Colors, print_system, print_error
from utils.file_utils import process_file_mentions


class CLI:
    """Klasa obsługująca interfejs wiersza poleceń."""
    
    def __init__(self, conversation):
        self.conversation = conversation
        self.auto_prompt = None
    
    def get_user_input(self):
        """Pobiera input od użytkownika lub używa auto_prompt."""
        if self.auto_prompt:
            user_input = self.auto_prompt
            self.auto_prompt = None
            print(f"{Colors.YELLOW}{Colors.BOLD}⚙️  Przekazuję logi procesów do Agenta...{Colors.ENDC}")
            return user_input, False
        
        user_input = input(f"{Colors.BLUE}{Colors.BOLD}🧑 Ty (@help):{Colors.ENDC} ")
        return user_input, True
    
    def process_input(self, user_input, is_manual):
        """Przetwarza input użytkownika i zwraca (should_continue, should_exit)."""
        if is_manual:
            # Obsługa komend wyjścia
            if user_input.strip().lower() in ['exit', 'quit']:
                print_system("Zakończono pracę. Do zobaczenia!")
                return False, True
            
            # Obsługa @help
            if user_input.strip() == '@help':
                self._show_help()
                return "", False
            
            # Puste inputy
            if not user_input.strip():
                return "", False
            
            # Przetwarzanie wzmianek o plikach i komend (@)
            user_input, commands_triggered = process_file_mentions(user_input)
            
            # Obsługa @clear
            if 'clear' in commands_triggered:
                self.conversation.clear()
                print_system("Pamięć agenta została wyczyszczona.")
                if not user_input.strip():
                    return "", False
            
            # Obsługa @compact
            if 'compact' in commands_triggered:
                current_tokens = self.conversation.get_token_count()
                self.conversation.compress(threshold=current_tokens - 500)
                if not user_input.strip():
                    return "", False
        
        return user_input, False
    
    def _show_help(self):
        """Wyświetla pomoc dostępną w trakcie konwersacji."""
        print(f"{Colors.CYAN}{Colors.BOLD}=== Pomoc Agenta DevOps ==={Colors.ENDC}")
        print("Dostępne komendy:")
        print("  @help        Wyświetla tę pomoc")
        print("  @plik        np. @README.md - wczytuje zawartość pliku")
        print("  @clear       Czyści pamięć (historię rozmowy)")
        print("  @compact    Kompresuje historię (oszczędza tokeny)")
        print("  exit / quit  Kończy pracę z agentem")
        print("  ?            Podczas pytania o zgodę - wyjaśnij komendę")
        print("  n            Podczas pytania o zgodę - odrzuć komendę")
        print()
    
    def set_auto_prompt(self, prompt):
        """Ustawia auto_prompt dla kolejnej iteracji."""
        self.auto_prompt = prompt
    
    def show_loading(self):
        """Wyświetla komunikat ładowania."""
        print(f"{Colors.GREEN}🤖 Agent zaciąga dane...{Colors.ENDC}", end="\r")
    
    def clear_loading(self):
        """Czyści linię ładowania."""
        import sys
        sys.stdout.write("\033[K")
