"""
Moduł obsługi wyjścia - przycinanie i zarządzanie dużymi danymi wyjściowymi.
"""
import sys
from ui.ui import Colors
from executor.executor_terminal import reset_terminal_state


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
