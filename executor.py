import re
import sys
import subprocess
import shlex
import platform
try:
    import termios
    import tty
    UNIX_AVAILABLE = True
except ImportError:
    UNIX_AVAILABLE = False  # Windows
from ui import Colors, print_error

def truncate_output(output, max_chars=15000, show_truncation_warning=True):
    """Przycina wyjście komendy z zachowaniem czytelności."""
    if len(output) <= max_chars:
        return output, False
    
    # Spróbuj przyciąć w miejscu łamania linii dla lepszej czytelności
    truncated = output[:max_chars]
    last_newline = truncated.rfind('\n')
    
    if last_newline > max_chars * 0.8:  # Jeśli ostatnia linia nie jest za krótka
        truncated = truncated[:last_newline]
    
    warning = f"\n\n[...WYJŚCIE PRZYCINĘTE z {len(output)} do {len(truncated)} znaków...]\n" if show_truncation_warning else ""
    return truncated + warning, True

def reset_terminal_state():
    """Resetuje stan terminala dla uniknięcia blokowania na Linux."""
    if not UNIX_AVAILABLE:
        return  # Windows nie potrzebuje resetu terminala
    
    try:
        # Przywróć ustawienia terminala
        if hasattr(sys.stdin, 'fileno'):
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            # Dodatkowo wymuś tryb kanoniczny
            new_settings = termios.tcgetattr(fd)
            new_settings[3] = new_settings[3] | termios.ICANON | termios.ECHO
            termios.tcsetattr(fd, termios.TCSADRAIN, new_settings)
    except:
        pass  # Ignoruj błędy na macOS/Windows
    
    # Ostateczność - uruchom stty sane (tylko Unix)
    try:
        subprocess.run(['stty', 'sane'], stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr, timeout=1)
    except:
        pass

def handle_large_output(output, cmd, is_timeout=False):
    """Obsługuje duże lub przerwane wyjście z opcjami dla użytkownika.
    Zwraca krotkę (output, should_analyze, skip_memory).
    - should_analyze: czy wysłać do agenta do analizy
    - skip_memory: czy pominąć dodawanie do historii czatu
    """
    lines_count = len(output.split('\n'))
    
    # Próg: 15k znaków, 200 linii lub jeśli komenda została przerwana (timeout)
    if not is_timeout and len(output) <= 15000 and lines_count < 200:
        return output, False, False
    
    reason = "została przerwana (timeout)" if is_timeout else f"ma {len(output)} znaków i {lines_count} linii"
    print(f"\n{Colors.YELLOW}📊 Wyjście komendy `{cmd}` {reason}.{Colors.ENDC}")
    print(f"{Colors.CYAN}Opcje:{Colors.ENDC}")
    print(f"  1) {Colors.GREEN}T{Colors.ENDC} - Przeanalizuj przycięte wyjście (pierwsze 15k znaków)")
    print(f"  2) {Colors.GREEN}P{Colors.ENDC} - Pokaż pierwsze 50 linii")
    print(f"  3) {Colors.GREEN}O{Colors.ENDC} - Pokaż ostatnie 50 linii")
    print(f"  4) {Colors.GREEN}N{Colors.ENDC} - Nie analizuj, pokaż surowe wyjście")
    print(f"  5) {Colors.GREEN}S{Colors.ENDC} - Zapisz do pliku i przeanalizuj plik")
    
    sys.stdout.flush()
    reset_terminal_state()  # Reset stanu terminala dla Linux
    
    while True:
        try:
            # Dodatkowe czyszczenie bufora dla bezpieczeństwa
            sys.stdin.flush()
            choice = input(f"{Colors.YELLOW}Wybierz opcję (T/P/O/N/S): {Colors.ENDC}").strip().lower()
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}Anulowano przetwarzanie dużego wyjścia.{Colors.ENDC}")
            return truncate_output(output)[0], True, False
        except (EOFError, OSError):
            # Obsługa błędów wejścia na Linux
            print(f"\n{Colors.YELLOW}Błąd wejścia - próbuję ponownie...{Colors.ENDC}")
            continue
        
        if choice in ['', 't']:
            return truncate_output(output)[0], True, False
        elif choice == 'p':
            lines = output.split('\n')[:50]
            result = '\n'.join(lines)
            if len(output.split('\n')) > 50:
                result += f"\n\n[...pierwsze 50 z {len(output.split('\n'))} linii...]"
            return result, True, False
        elif choice == 'o':
            lines = output.split('\n')[-50:]
            result = '\n'.join(lines)
            if len(output.split('\n')) > 50:
                result = f"\n\n[...ostatnie 50 z {len(output.split('\n'))} linii...]\n" + result
            return result, True, False
        elif choice == 'n':
            return output, False, True  # Nie analizuj, pomiń pamięć
        elif choice == 's':
            try:
                filename = f"output_{cmd.replace(' ', '_').replace('/', '_')[:20]}.txt"
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(output)
                print(f"{Colors.GREEN}✅ Zapisano wyjście do pliku: {filename}{Colors.ENDC}")
                return f"Wynik komendy `{cmd}` zapisano w pliku `{filename}` do analizy.", True, False
            except Exception as e:
                print(f"{Colors.RED}❌ Błąd zapisu pliku: {e}{Colors.ENDC}")
                return truncate_output(output)[0], True, False
        else:
            print(f"{Colors.RED}Nieprawidłowa opcja. Spróbuj ponownie.{Colors.ENDC}")

def is_dangerous_command(cmd):
    """Sprawdza czy komenda odnosi się do ścieżek/operacji uznanych za groźne."""
    # Ścieżki systemowe
    dangerous_paths = [
        '/etc', '/usr', '/bin', '/sbin', '/var', '/proc', '/sys', '/dev', '/root', '~'
    ]
    
    cmd_lower = cmd.lower()
    
    # Sprawdź path traversal - tylko w ścieżkach (poprzedzone spacją, / lub na początku)
    # Wyklucza false positive dla np. "echo '..'" lub "git log --oneline"
    if re.search(r'(?:^|\s|/|\'|")\.\.(?:$|[\s/\'"])', cmd):
        return True
        
    for path in dangerous_paths:
        # Sprawdzamy czy ścieżka występuje jako osobny "token" lub początek ścieżki
        # tzn. poprzedzona spacją lub będąca na początku, i zakończona spacją, slashem lub końcem linii
        pattern = rf"(^|\s){re.escape(path)}($|[\s/])"
        if re.search(pattern, cmd_lower):
            return True
            
    # Potencjalnie groźne modyfikatory plików poza projektem
    if 'rm ' in cmd_lower or 'chmod ' in cmd_lower or 'chown ' in cmd_lower:
        return True
        
    # Rozszerzona lista niebezpiecznych komend
    dangerous_commands = [
        # Modyfikatory plików/systemu
        'rm ', 'chmod ', 'chown ', 'dd', 'mkfs', 'fdisk', 'parted',
        # Zarządzanie systemem
        'shutdown', 'reboot', 'halt', 'poweroff', 'systemctl',
        # Procesy
        'kill ', 'pkill', 'killall',
        # Eksfiltracja danych / sieci
        'curl ', 'wget ', 'nc ', 'netcat', 'scp ', 'rsync',
        # Wykonywanie kodu / injection
        'python', 'python3', 'perl ', 'ruby ', 'node ', 'php ',
        'eval ', 'exec ', 'source ',
        # Uprawnienia
        'sudo ', 'su ', 'doas ',
        # Sieć/firewall
        'iptables', 'firewall-cmd', 'ufw',
        # Automatyzacja/zadania
        'crontab', 'at ',
        # Zarządzanie użytkownikami
        'useradd', 'userdel', 'usermod', 'passwd',
        # Inne niebezpieczne
        'mv /', 'cp /', 'cat /etc/', 'vim /etc/', 'nano /etc/',
        '>', '>>', '|', '&&', '||',  # przekierowania i łańcuchy komend
    ]
    
    for dangerous in dangerous_commands:
        if dangerous in cmd_lower:
            return True
        
    return False

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
            print(f"Uruchamiam podproces (limit {timeout_sec}s, czekaj...)...")
            timed_out = False
            try:
                # Bezpieczniejsze wykonanie komendy bez shell=True
                # Sprawdź czy komenda zawiera przekierowania lub potoki
                has_shell_chars = any(c in cmd for c in ['|', '&&', '||', '>', '>>', '<', '$(', '`'])
                
                if has_shell_chars:
                    # Komenda złożona - wymaga shella, ale z dodatkowym ostrzeżeniem
                    print(f"{Colors.YELLOW}⚠️ Komenda zawiera potoki/przekierowania - wymaga shell. Dodatkowa ostrożność!{Colors.ENDC}")
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
            except Exception as e:
                print(f"{Colors.RED}Błąd API Pythona uderzający poleceniem: {e}{Colors.ENDC}")
                auto_prompt = f"Polecenie `{cmd}` zakończyło się błędem środowiska: {e}"

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
