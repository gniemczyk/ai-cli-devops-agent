import re
import sys
import subprocess
from ui import Colors, print_error

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
            print(f"Uruchamiam podproces w środowisku...")
            try:
                res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                out_payload = res.stdout + res.stderr
                
                if not out_payload.strip():
                    out_payload = "[Polecenie zakończyło się cichym sukcesem. Brak wyjścia stdout.]"
                    
                choice_analysis = input(f"{Colors.YELLOW}Czy przekazać ten wynik do Agenta na analizę? [T/n]: {Colors.ENDC}").strip().lower()

                if len(out_payload) > 15000:
                    out_payload = out_payload[:15000] + "\n...[UCIAKNIĘTO LOGI SYSTEMOWE Z POWODU LIMITU]"

                if choice_analysis in ['', 't', 'y', 'tak', 'yes']:
                    print(f"{Colors.YELLOW}✔ Wyjście z konsoli: {len(out_payload)} znaków. Generuję analizę...{Colors.ENDC}\n")
                    auto_prompt = f"Wynik wywołania `{cmd}`:\n```\n{out_payload}\n```\n(przeanalizuj wyjście)"
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
