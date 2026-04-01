"""
Moduł wykonywania komend - główna logika obsługi <execute>.
"""
import re
import sys
import subprocess
import shlex
import platform
from ui import Colors, print_error
from executor_terminal import reset_terminal_state
from executor_security import is_dangerous_command
from executor_output import handle_large_output


def handle_agent_commands(agent_reply, messages, client):
    """
    Sprawdza, czy w odpowiedzi są tagi <execute>.
    Uruchamia interaktywne sprawdzanie i wywołuje polecenie.
    Zwraca krotkę (auto_prompt, executed_something)
    """
    commands = re.findall(r'<execute>(.*?)</execute>', agent_reply, re.DOTALL | re.IGNORECASE)
    
    auto_prompt = None
    executed_something = False
    
    for cmd in commands:
        cmd = cmd.strip()
        if not cmd:
            continue
            
        executed_something = True
        
        is_dangerous = is_dangerous_command(cmd)
        if is_dangerous:
            print(f"\n{Colors.RED}{Colors.BOLD}╔═══════════════════════════════════════════════════════════════╗{Colors.ENDC}")
            print(f"{Colors.RED}{Colors.BOLD}║   ⚠️  OSTRZEŻENIE: KOMENDA SYSTEMOWA (ZAKAZANA ŚCIEŻKA)        ║{Colors.ENDC}")
            print(f"{Colors.RED}{Colors.BOLD}╚═══════════════════════════════════════════════════════════════╝{Colors.ENDC}")
            print(f"{Colors.RED}{Colors.BOLD}Agent żąda dostępu do wrażliwego obszaru systemu!{Colors.ENDC}")
        else:
            print(f"{Colors.RED}{Colors.BOLD}⚠️ Agent żąda dostępu do powłoki!{Colors.ENDC}")
            
        print(f"Będzie wykonane: {Colors.CYAN}{Colors.BOLD}> {cmd} <{Colors.ENDC}")
        
        # Reset terminala przed każdym input (dla Linux)
        reset_terminal_state()
        
        while True:
            choice = input(f"{Colors.RED}Zezwolić? (T/n/? - wyjaśnij): {Colors.ENDC}").strip().lower()
            if choice == '?':
                print(f"{Colors.GREEN}🤖 Agent przygotowuje wyjaśnienie polecenia...{Colors.ENDC}", end="\r")
                explain_msgs = messages + [{"role": "user", "content": f"Wyjaśnij zwięźle i krótko, co dokładnie robi wiersz poleceń: `{cmd}`"}]
                explain_resp = client.chat_completion(explain_msgs)
                sys.stdout.write("\033[K")
                if "error" not in explain_resp and "choices" in explain_resp and len(explain_resp["choices"]) > 0:
                    print(f"\n{Colors.CYAN}{Colors.BOLD}--- WYJAŚNIENIE KOMENDY ---{Colors.ENDC}")
                    print(explain_resp["choices"][0]["message"]["content"].strip())
                    print(f"{Colors.CYAN}{Colors.BOLD}---------------------------{Colors.ENDC}\n")
                else:
                    err = explain_resp.get("error", "Nieznany błąd API")
                    print_error(f"Nie udało się pobrać wyjaśnienia. ({err})")
            elif choice in ['', 't', 'y', 'tak', 'yes'] and is_dangerous:
                # Drugie powiadomienie dla niebezpiecznych komend
                print(f"\n{Colors.RED}{Colors.BOLD}‼️  CZY NA PEWNO? Operator bierze na siebie PEŁNĄ ODPOWIEDZIALNOŚĆ{Colors.ENDC}")
                print(f"{Colors.RED}{Colors.BOLD}za skutki tej komendy w systemie. (T/n): {Colors.ENDC}", end="")
                sys.stdout.flush()
                reset_terminal_state()  # Reset przed drugim input
                choice2 = input().strip().lower()
                if choice2 in ['t', 'y', 'tak', 'yes']:
                    choice = 't' # Przechodzimy dalej
                    break
                else:
                    choice = 'n' # Odmowa w drugim kroku
                    break
            else:
                break
        
        if choice in ['', 't', 'y', 'tak', 'yes']:
            timeout_sec = 10
            print(f"Uruchamiam podproces (limit {timeout_sec}s, czekaj)...")
            timed_out = False
            out_payload = ""  # Inicjalizacja przed try
            try:
                # Bezpieczniejsze wykonanie komendy bez shell=True
                # Sprawdź czy komenda zawiera przekierowania, potoki lub wywołanie polecenia wbudowanego shella
                shell_builtins = ['cd', 'source', 'export', 'alias', 'set', 'unset', 'history', 'type']
                has_shell_chars = any(c in cmd for c in ['|', '&&', '||', '>', '>>', '<', '$(', '`'])
                is_shell_builtin = cmd.strip().split()[0] in shell_builtins if cmd.strip() else False
                
                if has_shell_chars or is_shell_builtin:
                    # Komenda złożona lub wbudowana - wymaga shella
                    print(f"{Colors.YELLOW}⚠️ Komenda wymaga powłoki (shell). Dodatkowa ostrożność!{Colors.ENDC}")
                    # Wybierz odpowiedni shell dla systemu
                    if platform.system() == 'Windows':
                        shell_cmd = ['cmd', '/c', cmd]
                    else:
                        shell_cmd = ['/bin/bash', '-c', cmd]
                    res = subprocess.run(
                        shell_cmd,
                        stdout=subprocess.PIPE, 
                        stderr=subprocess.PIPE, 
                        universal_newlines=True, 
                        timeout=timeout_sec
                    )
                else:
                    # Prosta komenda - użyj shlex.split dla bezpieczeństwa
                    try:
                        args = shlex.split(cmd)
                        res = subprocess.run(
                            args, 
                            stdout=subprocess.PIPE, 
                            stderr=subprocess.PIPE, 
                            universal_newlines=True, 
                            timeout=timeout_sec
                        )
                    except ValueError as e:
                        # Jeśli shlex.split nie radzi sobie z komendą, użyj shella jako fallback
                        print(f"{Colors.YELLOW}⚠️ Komenda wymaga shell: {e}{Colors.ENDC}")
                        # Wybierz odpowiedni shell dla systemu
                        if platform.system() == 'Windows':
                            shell_cmd = ['cmd', '/c', cmd]
                        else:
                            shell_cmd = ['/bin/bash', '-c', cmd]
                        res = subprocess.run(
                            shell_cmd,
                            stdout=subprocess.PIPE, 
                            stderr=subprocess.PIPE, 
                            universal_newlines=True, 
                            timeout=timeout_sec
                        )
                out_payload = res.stdout + res.stderr
            except subprocess.TimeoutExpired as te:
                timed_out = True
                
                # KRYTYCZNE: Natychmiast zresetuj terminal po timeout
                reset_terminal_state()
                
                # Przechwyć to co się udało zebrać, dbając o typ danych (str vs bytes)
                raw_stdout = te.stdout if te.stdout is not None else ""
                raw_stderr = te.stderr if te.stderr is not None else ""
                
                if isinstance(raw_stdout, bytes):
                    raw_stdout = raw_stdout.decode(errors="replace")
                if isinstance(raw_stderr, bytes):
                    raw_stderr = raw_stderr.decode(errors="replace")
                    
                out_payload = raw_stdout + raw_stderr
                print(f"{Colors.YELLOW}⏱️  Polecenie przekroczyło limit {timeout_sec}s i zostało zatrzymane.{Colors.ENDC}")
            except FileNotFoundError as e:
                # Komenda nie istnieje w systemie (np. journalctl na macOS)
                out_payload = f"[BŁĄD: Komenda '{cmd.split()[0]}' nie została znaleziona w systemie. Może wymagać instalacji lub jest niedostępna na tej platformie.]"
                print(f"{Colors.RED}❌ Komenda nie istnieje: {e}{Colors.ENDC}")
            except Exception as e:
                print(f"{Colors.RED}Błąd API Pythona uderzający poleceniem: {e}{Colors.ENDC}")
                out_payload = f"[Błąd wykonania: {e}]"

            try:
                if not out_payload.strip():
                    out_payload = "[Polecenie zakończyło się cichym sukcesem. Brak wyjścia stdout.]"

                if timed_out:
                    out_payload += f"\n\n[UWAGA: Polecenie zostało przerwane po {timeout_sec}s limitu czasu. Powyżej znajduje się częściowy wynik.]"

                # Obsługa dużych lub przerwanych wyjść
                processed_output, should_analyze, skip_memory = handle_large_output(out_payload, cmd, is_timeout=timed_out)
                
                if should_analyze:
                    print(f"{Colors.YELLOW}✔ Przetworzono wyjście: {len(processed_output)} znaków. Generuję analizę...{Colors.ENDC}\n")
                    auto_prompt = f"Wynik wywołania `{cmd}`:\n```\n{processed_output}\n```\n(przeanalizuj wyjście)"
                elif not skip_memory:
                    # Tylko wyświetl wynik, ale zapisz w pamięci (dla małych wyjść)
                    print(f"\n{Colors.CYAN}{Colors.BOLD}--- WYNIK KOMENDY `{cmd}` ---{Colors.ENDC}")
                    print(out_payload.strip())
                    print(f"{Colors.CYAN}{Colors.BOLD}----------------------------------{Colors.ENDC}")
                    
                    messages.append({"role": "user", "content": f"Uruchomiono wynik komendy systemowej `{cmd}`:\n```\n{out_payload}\n```\nTylko odnotuj to w pamięci chmurowej, omijając analizę na ekran zaoszczędzimy żądanie."})
                    messages.append({"role": "assistant", "content": "Zrozumiałem."})
                else:
                    # Opcja N - tylko wyświetl, bez pamięci
                    print(f"\n{Colors.CYAN}{Colors.BOLD}--- WYNIK KOMENDY `{cmd}` ---{Colors.ENDC}")
                    print(out_payload.strip())
                    print(f"{Colors.CYAN}{Colors.BOLD}----------------------------------{Colors.ENDC}")
            except Exception as e:
                print(f"{Colors.RED}Błąd API Pythona uderzający poleceniem: {e}{Colors.ENDC}")
                auto_prompt = f"Polecenie `{cmd}` zakończyło się błędem środowiska: {e}"

            # Reset stanu terminala po wykonaniu komendy systemowej
            reset_terminal_state()
            sys.stdin.flush()
        else:
            print(f"{Colors.YELLOW}❌ Zablokowałeś wykonanie polecenia. Wracam do nasłuchu...{Colors.ENDC}")
            messages.append({"role": "user", "content": f"[SYSTEM]: Użytkownik odmówił wykonania komendy `{cmd}`. Nie proponuj jej ponownie bez prośby."})
            messages.append({"role": "assistant", "content": "Zrozumiałem."})
            auto_prompt = None
        
    return auto_prompt, executed_something
