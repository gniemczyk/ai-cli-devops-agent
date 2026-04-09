#!/usr/bin/env python3
import sys
from utils.env_loader import validate_and_setup
from core.client import APIClient
from config import DEFAULT_PROVIDER
from ui.ui import Colors, print_system, print_error
from executor.executor import reset_terminal_state
from core.conversation import Conversation
from ui.cli import CLI
from core.response_handler import ResponseHandler


def print_help():
    print(f"{Colors.CYAN}{Colors.BOLD}=== Lokalny Agent DevOps (AI CLI) ==={Colors.ENDC}")
    print("Użycie: python3 agent.py")
    print("\nOpcje argumentów:")
    print("  -h, --help    Wyświetla tę pomoc")
    print("\nFunkcje dostępne w trakcie działania chatu:")
    print("  @<ścieżka>    np. @README.md lub @agent.py - wczytuje zawartość pliku i dołącza ją do zapytania")
    print("  @clear        Czyści pamięć (historię rozmowy) agenta")
    print("  @compact     Kompresuje historię (zachowuje podsumowania, oszczędza tokeny)")
    print("  exit / quit   Kończy pracę z agentem")
    print("  ?             Podczas pytania o zgodę na polecenie (T/n/?) wysyła prośbę o jego objaśnienie")
    print("  n             Odrzuca komendę proponowaną przez ai i błyskawicznie wraca do oczekiwania na tekst")


def main():
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help']:
        print_help()
        sys.exit(0)

    print(f"\n{Colors.CYAN}{Colors.BOLD}=== Lokalny Agent DevOps (AI CLI) ==={Colors.ENDC}")
    print_system("Inicjalizacja środowiska agenta...")
    
    try:
        active_providers = validate_and_setup()
        client = APIClient(provider_name=DEFAULT_PROVIDER, providers_config=active_providers)
    except Exception as e:
        print_error(f"Nie udało się skonfigurować klienta: {e}")
        sys.exit(1)
        
    print_system(f"Aktywny provider: {Colors.BOLD}{DEFAULT_PROVIDER.upper()}{Colors.ENDC}")
    print_system(f"Używany model: {Colors.BOLD}{client.model}{Colors.ENDC}")
    print_system("Napisz 'exit' lub naciśnij Ctrl+C, aby wyjść.\n")

    conversation = Conversation(client)
    cli = CLI(conversation)
    response_handler = ResponseHandler(conversation, client)

    while True:
        try:
            user_input, is_manual = cli.get_user_input()
            
            if is_manual:
                processed_input, should_exit = cli.process_input(user_input, is_manual)
                if should_exit:
                    break
                if not processed_input:
                    continue
                user_input = processed_input
            
            conversation.add_user_message(user_input)
            conversation.compress()
            
            cli.show_loading()
            response = client.chat_completion(conversation.get_messages())
            cli.clear_loading()
            
            success, auto_prompt = response_handler.handle_response(response)
            if not success:
                continue
            
            if auto_prompt:
                cli.set_auto_prompt(auto_prompt)

        except KeyboardInterrupt:
            reset_terminal_state()
            print_system("\nZakończono przez użytkownika (Ctrl+C).")
            break
        except EOFError:
            reset_terminal_state()
            print_system("\nZakończono (EOF).")
            break
        except Exception as e:
            print_error(f"Wystąpił krytyczny wyjątek w pętli agenta: {e}")


if __name__ == "__main__":
    main()
