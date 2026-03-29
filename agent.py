#!/usr/bin/env python3
import sys
import json
from env_loader import validate_and_setup
from client import APIClient
from config import DEFAULT_PROVIDER, MEMORY_SOFT_LIMIT
from ui import Colors, print_system, print_error
from file_utils import process_file_mentions
from executor import handle_agent_commands, reset_terminal_state
from skills import get_system_prompt_addon

def print_help():
    print(f"{Colors.CYAN}{Colors.BOLD}=== Lokalny Agent DevOps (AI CLI) ==={Colors.ENDC}")
    print("Użycie: python3 agent.py")
    print("\nOpcje argumentów:")
    print("  -h, --help    Wyświetla tę pomoc")
    print("\nFunkcje dostępne w trakcie działania chatu:")
    print("  @<ścieżka>    np. @~/.bashrc lub @agent.py - wczytuje zawartość pliku i dołącza ją do zapytania")
    print("  @clear        Czyści pamięć (historię rozmowy) agenta")
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
        # Inicjalizacja środowiska i pobranie skonfigurowanych providerów
        active_providers = validate_and_setup()
        client = APIClient(provider_name=DEFAULT_PROVIDER, providers_config=active_providers)
    except Exception as e:
        print_error(f"Nie udało się skonfigurować klienta: {e}")
        sys.exit(1)
        
    print_system(f"Aktywny provider: {Colors.BOLD}{DEFAULT_PROVIDER.upper()}{Colors.ENDC}")
    print_system(f"Używany model: {Colors.BOLD}{client.model}{Colors.ENDC}")
    print_system("Napisz 'exit' lub naciśnij Ctrl+C, aby wyjść.\n")

    base_prompt = """Jesteś asystentem DevOps o potężnych możliwościach. Jeśli chcesz pozyskać informacje o systemie operacyjnym (np. uruchomić 'docker ps', 'ps aux', 'ls -la'), wygeneruj komendę ujętą dokładnie w specjalne tagi XML: <execute>TWOJA_KOMENDA</execute>.

Użytkownik zostanie natychmiast zapytany o interaktywną zgodę na jej wykonanie. Gdy wyrazi zgodę, komenda zostaje wykonana ukradkiem w tle, a TY zaraz potem otrzymasz od systemu wynik tekstowy tej komendy - wtedy dokonasz dogłębnej analizy dla użytkownika! Wydawaj maksymalnie jedną komendę w okienku."""
    
    skills_prompt = get_system_prompt_addon()
    
    messages = [
        {"role": "system", "content": base_prompt + "\n" + skills_prompt}
    ]
    
    system_message = messages[0]

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
                
                # Przetwarzanie wzmianek o plikach i komend (@)
                user_input, commands_triggered = process_file_mentions(user_input)

                if 'clear' in commands_triggered:
                    messages = [system_message]
                    print_system("Pamięć agenta została wyczyszczona.")
                    if not user_input.strip(): # Jeśli wpisano tylko @clear, wracamy do początku pętli
                        continue

            messages.append({"role": "user", "content": user_input})
            print(f"{Colors.GREEN}🤖 Agent zaciąga dane...{Colors.ENDC}", end="\r")
            
            response = client.chat_completion(messages)
            sys.stdout.write("\033[K")
            
            # Pobieramy info o tokenach
            tokens_count = response.get("_total_tokens", 0)
            token_info = f" ({tokens_count}t)" if tokens_count > 0 else ""

            if "error" in response:
                print_error(response["error"])
                messages.pop()
                continue
            
            if "choices" in response and len(response["choices"]) > 0:
                agent_reply = response["choices"][0]["message"]["content"]
                
                print(f"{Colors.GREEN}{Colors.BOLD}🤖 Agent{token_info}:{Colors.ENDC}\n{agent_reply}\n")
                
                if tokens_count > MEMORY_SOFT_LIMIT:
                    print(f"{Colors.YELLOW}⚠️  Pamięć agenta jest duża ({tokens_count} tokenów). Rozważ zresetowanie sesji (Ctrl+C i ponowne uruchomienie), aby uniknąć błędów lub wysokich kosztów.{Colors.ENDC}\n")

                messages.append({"role": "assistant", "content": agent_reply})
                
                next_auto_prompt, executed_something = handle_agent_commands(agent_reply, messages, client)
                if executed_something:
                    auto_prompt = next_auto_prompt
                    
            else:
                print_error(f"Dziwny format odpowiedzi z serwera:\n{json.dumps(response, indent=2)}")

        except KeyboardInterrupt:
            reset_terminal_state()  # Reset terminala na Linux
            print_system("\nZakończono przez użytkownika (Ctrl+C).")
            break
        except EOFError:
            reset_terminal_state()  # Reset terminala na Linux
            print_system("\nZakończono (EOF).")
            break
        except Exception as e:
            print_error(f"Wystąpił krytyczny wyjątek w pętli agenta: {e}")

if __name__ == "__main__":
    main()
