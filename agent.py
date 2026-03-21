#!/usr/bin/env python3
import sys
import json
from client import APIClient
from config import DEFAULT_PROVIDER
from ui import Colors, print_system, print_error
from file_utils import process_file_mentions
from executor import handle_agent_commands

def print_help():
    print(f"{Colors.CYAN}{Colors.BOLD}=== Lokalny Agent DevOps (AI CLI) ==={Colors.ENDC}")
    print("Użycie: python3 agent.py")
    print("\nOpcje argumentów:")
    print("  -h, --help    Wyświetla tę pomoc")
    print("\nFunkcje dostępne w trakcie działania chatu:")
    print("  @<ścieżka>    np. @~/.bashrc lub @agent.py - wczytuje zawartość pliku i dołącza ją do zapytania")
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
        client = APIClient(provider_name=DEFAULT_PROVIDER)
    except Exception as e:
        print_error(f"Nie udało się skonfigurować klienta: {e}")
        sys.exit(1)
        
    print_system(f"Aktywny provider: {Colors.BOLD}{DEFAULT_PROVIDER.upper()}{Colors.ENDC}")
    print_system(f"Używany model: {Colors.BOLD}{client.model}{Colors.ENDC}")
    print_system("Napisz 'exit' lub naciśnij Ctrl+C, aby wyjść.\n")

    messages = [
        {"role": "system", "content": "Jesteś asystentem DevOps o potężnych możliwościach. Jeśli chcesz pozyskać informacje o systemie operacyjnym (np. uruchomić 'docker ps', 'ps aux', 'ls -la'), wygeneruj komendę ujętą dokładnie w specjalne tagi XML: <execute>TWOJA_KOMENDA</execute>.\n\nUżytkownik zostanie natychmiast zapytany o interaktywną zgodę na jej wykonanie. Gdy wyrazi zgodę, komenda zostaje wykonana ukradkiem w tle, a TY zaraz potem otrzymasz od systemu wynik tekstowy tej komendy - wtedy dokonasz dogłębnej analizy dla użytkownika! Wydawaj maksylanie jedną komendę w okienku."}
    ]

    auto_prompt = None

    while True:
        try:
            if auto_prompt:
                user_input = auto_prompt
                auto_prompt = None
                print(f"{Colors.YELLOW}{Colors.BOLD}⚙️  Przekazuję logi procesów do Agenta...{Colors.ENDC}")
            else:
                user_input = input(f"{Colors.BLUE}{Colors.BOLD}🧑 Ty:{Colors.ENDC} ")
                
                if user_input.strip().lower() in ['exit', 'quit']:
                    print_system("Zakończono pracę. Do zobaczenia!")
                    break
                    
                if not user_input.strip():
                    continue
                
                user_input = process_file_mentions(user_input)

            messages.append({"role": "user", "content": user_input})
            print(f"{Colors.GREEN}🤖 Agent zaciąga dane...{Colors.ENDC}", end="\r")
            
            response = client.chat_completion(messages)
            sys.stdout.write("\033[K")
            
            if "error" in response:
                print_error(response["error"])
                messages.pop()
                continue
            
            if "choices" in response and len(response["choices"]) > 0:
                agent_reply = response["choices"][0]["message"]["content"]
                
                print(f"{Colors.GREEN}{Colors.BOLD}🤖 Agent:{Colors.ENDC}\n{agent_reply}\n")
                messages.append({"role": "assistant", "content": agent_reply})
                
                next_auto_prompt, executed_something = handle_agent_commands(agent_reply, messages, client)
                if executed_something:
                    auto_prompt = next_auto_prompt
                    
            else:
                print_error(f"Dziwny format odpowiedzi z serwera:\n{json.dumps(response, indent=2)}")

        except KeyboardInterrupt:
            print_system("\nZakończono przez użytkownika (Ctrl+C).")
            break
        except EOFError:
            print_system("\nZakończono (EOF).")
            break
        except Exception as e:
            print_error(f"Wystąpił krytyczny wyjątek w pętli agenta: {e}")

if __name__ == "__main__":
    main()
