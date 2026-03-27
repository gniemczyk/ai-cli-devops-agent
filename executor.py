import re
import sys
import subprocess
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

def handle_large_output(output, cmd):
    """Obsługuje duże wyjście z opcjami dla użytkownika."""
    if len(output) <= 15000:
        return output, False
    
    print(f"\n{Colors.YELLOW}📊 Wyjście komendy `{cmd}` ma {len(output)} znaków.{Colors.ENDC}")
    print(f"{Colors.CYAN}Opcje:{Colors.ENDC}")
    print(f"  1) {Colors.GREEN}T{Colors.ENDC} - Przeanalizuj przycięte wyjście (pierwsze 15k znaków)")
    print(f"  2) {Colors.GREEN}P{Colors.ENDC} - Pokaż pierwsze 50 linii")
    print(f"  3) {Colors.GREEN}O{Colors.ENDC} - Pokaż ostatnie 50 linii")
    print(f"  4) {Colors.GREEN}N{Colors.ENDC} - Nie analizuj, pokaż surowe wyjście")
    print(f"  5) {Colors.GREEN}S{Colors.ENDC} - Zapisz do pliku i przeanalizuj plik")
    
    while True:
        choice = input(f"{Colors.YELLOW}Wybierz opcję (T/P/O/N/S): {Colors.ENDC}").strip().lower()
        
        if choice in ['', 't']:
            return truncate_output(output)[0], True
        elif choice == 'p':
            lines = output.split('\n')[:50]
            result = '\n'.join(lines)
            if len(output.split('\n')) > 50:
                result += f"\n\n[...pierwsze 50 z {len(output.split('\n'))} linii...]"
            return result, True
        elif choice == 'o':
            lines = output.split('\n')[-50:]
            result = '\n'.join(lines)
            if len(output.split('\n')) > 50:
                result = f"\n\n[...ostatnie 50 z {len(output.split('\n'))} linii...]\n" + result
            return result, True
        elif choice == 'n':
            return output, False
        elif choice == 's':
            try:
                filename = f"output_{cmd.replace(' ', '_').replace('/', '_')[:20]}.txt"
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(output)
                print(f"{Colors.GREEN}✅ Zapisano wyjście do pliku: {filename}{Colors.ENDC}")
                return f"Wynik komendy `{cmd}` zapisano w pliku `{filename}` do analizy.", True
            except Exception as e:
                print(f"{Colors.RED}❌ Błąd zapisu pliku: {e}{Colors.ENDC}")
                return truncate_output(output)[0], True
        else:
            print(f"{Colors.RED}Nieprawidłowa opcja. Spróbuj ponownie.{Colors.ENDC}")

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
        print(f"{Colors.RED}{Colors.BOLD}⚠️ Agent żąda dostępu do powłoki!{Colors.ENDC}")
        print(f"Będzie wykonane: {Colors.CYAN}{Colors.BOLD}> {cmd} <{Colors.ENDC}")
        
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
            else:
                break
        
        if choice in ['', 't', 'y', 'tak', 'yes']:
            timeout_sec = 10
            print(f"Uruchamiam podproces (limit {timeout_sec}s, czekaj...)...")
            timed_out = False
            try:
                res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout_sec)
                out_payload = res.stdout + res.stderr
            except subprocess.TimeoutExpired as te:
                timed_out = True
                
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
                break

            try:
                if not out_payload.strip():
                    out_payload = "[Polecenie zakończyło się cichym sukcesem. Brak wyjścia stdout.]"

                if timed_out:
                    out_payload += f"\n\n[UWAGA: Polecenie zostało przerwane po {timeout_sec}s limitu czasu. Powyżej znajduje się częściowy wynik.]"

                # Obsługa dużych wyjść
                processed_output, should_analyze = handle_large_output(out_payload, cmd)
                
                if should_analyze:
                    print(f"{Colors.YELLOW}✔ Przetworzono wyjście: {len(processed_output)} znaków. Generuję analizę...{Colors.ENDC}\n")
                    auto_prompt = f"Wynik wywołania `{cmd}`:\n```\n{processed_output}\n```\n(przeanalizuj wyjście)"
                else:
                    print(f"\n{Colors.CYAN}{Colors.BOLD}--- WYNIK KOMENDY `{cmd}` ---{Colors.ENDC}")
                    print(out_payload.strip())
                    print(f"{Colors.CYAN}{Colors.BOLD}----------------------------------{Colors.ENDC}")
                    
                    messages.append({"role": "user", "content": f"Uruchomiono wynik komendy systemowej `{cmd}`:\n```\n{out_payload}\n```\nTylko odnotuj to w pamięci chmurowej, omijając analizę na ekran zaoszczędzimy żądanie."})
                    messages.append({"role": "assistant", "content": "Zrozumiałem."})
            except Exception as e:
                print(f"{Colors.RED}Błąd API Pythona uderzający poleceniem: {e}{Colors.ENDC}")
                auto_prompt = f"Polecenie `{cmd}` zakończyło się błędem środowiska: {e}"
        else:
            print(f"{Colors.YELLOW}❌ Zablokowałeś wykonanie polecenia. Wracam do nasłuchu...{Colors.ENDC}")
            messages.append({"role": "user", "content": f"[SYSTEM]: Użytkownik odmówił wykonania komendy `{cmd}`. Nie proponuj jej ponownie bez prośby."})
            messages.append({"role": "assistant", "content": "Zrozumiałem."})
            auto_prompt = None
        
        break
        
    return auto_prompt, executed_something
