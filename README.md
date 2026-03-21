# AI CLI DevOps Agent

Lekki, interaktywny agent konsolowy (CLI) napisany w czystym języku Python **bez zewnętrznych zależności** (brak konieczności używania `pip`). Zapewnia łatwą w integracji architekturę do bezpiecznej komunikacji z chmurowymi modelami LLM. Domyślnie wykorzystuje interfejs OpenAI API udostępniany w usłudze Cloudflare AI Gateway.

> 💡 **Darmowy limit Cloudflare AI:** Cloudflare oferuje na darmowym koncie bezpłatny budżet wynoszący **10 000 Neurons dziennie**. Należy pamiętać, że *Neurons* są kalkulowane inaczej niż klasyczne tokeny. Jeśli limit dzienny zostanie wyczerpany na darmowym planie, API po prostu zwróci błąd limitu i **Cloudflare nie pobierze żadnych dodatkowych opłat**.


## 🛠 Struktura Projektu

- `agent.py` - Główny plik wejściowy (entrypoint). Inicjalizuje pętlę chatu i łączy wszystkie moduły ze sobą.
- `config.py` - Narzędzia konfiguracyjne (wbudowany parser zmiennych lokalnych `.env`, parametry i adresy API).
- `client.py` - Klient HTTP (wykorzystujący bezpiecznie standardowe `urllib`) dla modeli zgodnych z OpenAI API.
- `executor.py` - Zewnętrzny silnik Auto-DevOps. Czuwa nad poleceniami (`<execute>`), pyta o autoryzację (`T/n/?`), uruchamia procesy shella i łapie ich rezultaty.
- `file_utils.py` - Mały parser tekstu odpowiadający za sprytne dołączanie lokalnych plików do chatu na hasło `@plik`.
- `ui.py` - Moduł zarządzający szatą graficzną w terminalu (palety Color i formatowanie wyskakujących zdarzeń).

## 🚀 Instalacja i Uruchomienie

**1. Wymagania wstępne**
Projekt wymaga jedynie zainstalowanego interpretera Python (z zaleceniem minimalnej wersji 3.6+). Brak konieczności zestawiania środowisk wirtualnych lub paczek oprogramowania.

**2. Autoryzacja API (Konfiguracja klucza)**
Agent wymaga tokenu logowania odpowiedniego dostawcy usług, zabezpieczonego we wbudowanym module środowiskowym poza przestrzenią systemu kontroli wersji Git (plik `.gitignore`).

W katalogu docelowym projektu utworzono pomocniczy ekosystem:
- `.env.example` - zarys pożądanej struktury zmiennych wymaganych do autoryzacji.
- `.env` - właściwy, docelowy plik, który weryfikuje parser zagnieżdżony w agencie. 

Instrukcja dodawania klucza API i numeru konta:
1. Skopiuj wzór z `.env.example` do nowego ukrytego pliku `.env`.
2. Zmodyfikuj frazę `TUTAJ_WKLEJ_SWOJ_TOKEN` wprowadzając docelowy wygenerowany token Cloudflare.
3. Podmień wartość `CF_NR_ACCOOUNT` wstawiając swój kod konta Cloudflare (ID konta wyświetlane m.in. w url endpointu API).
4. Zapisz plik.

**3. Uruchamianie Agenta**
Inicjalizacja odbywa się przez wydanie standardowego wywołania Pythona z konsoli w głównym folderze roboczym:
```bash
python3 agent.py
```
*Do przerwania wątku roboczego użyj w standardowym wejściu słowa `exit`, lub przerwania `Ctrl+C`.*

**4. Rozwiązywanie problemów (Certyfikaty SSL)**
Aplikacja podejmuje domyślne, silne próby egzekwowania pełnego szyfrowania za pomocą certyfikatów z poziomu systemu operacyjnego. Brak zaktualizowanych certyfikatów bazowych na maszynie objawi się potężnym komunikatem z żółtym ostrzeżeniem w konsoli – w locie odpalane jest wtedy tzw. wbudowane ominięcie weryfikacji awaryjnej (niezabezpieczonym ruchem publicznym).
*   **Dla instancji macOS:** Zależności Apple nie podpinają pęku Keychain do języka *Python*. Jeśli widzisz komunikat o braku certyfikatu, wykonaj poniższą komendę jednorazową w terminalu i napisz zapytanie jeszcze raz:
    ```bash
    open "/Applications/Python "*"/Install Certificates.command"
    ```
*   **Dla linuksowych instancji (Debian / Ubuntu):** Odmowa połączeń szyfrowanych wynika bezpośrednio ze ślepoty systemu. Należy po prostu zaktualizować paczkę systemową:
    ```bash
    sudo apt update && sudo apt install ca-certificates
    ```

## ⌨️ Funkcje czatu i Narzędzia (Rozszerzenia)

Projekt udostępnia szereg wbudowanych narzędzi ułatwiających analizę usterek i usprawniających pracę z systemem docelowym. Wystarczy uruchomić program z odpowiednią flagą:
- `python3 agent.py --help` (lub `-h`) - wyświetla pomoc z wprowadzonymi nowościami w zachowaniu i komendach terminalowych.

**Kluczowe modyfikatory dostępne podczas wprowadzania tekstu w konsoli:**
- `@ścieżka/do/pliku` – wpisanie przedrostka `@` oraz ścieżki (np. `@~/.bashrc` czy `@agent.py`) sprawi, że system lokalnie na dysku automatycznie wczyta treść tego pliku i niejawnie dołączy ją do Twojego zapytania przed wylotem do API. Wygodnie jest po prostu napisać: *"Spróbuj zoptymalizować dla mnie ten plik @agent.py"*.
- `Zezwolić? (T/n/?)` – gdy agent domofonu zaproponuje wykonanie polecenia systemowego, możesz obok potwierdzenia i odrzucenia - podać **Znak zapytania (`?`)**. Model LLM wygeneruje dedykowane, opisowe wytłumaczenie co dana komenda robi chroniąc twój komputer przed groźnymi incydentami i oszczędzając czas w man page. Otrzymasz ten komunikat od razu i agent następnie poczeka upewniony na poprawną odpowiedź zgodną z wolą.
- `Błyskawiczna odmowa (n)` – Wpisanie `n` na propozycję agenta w 100% obala jego argument, ucinając ścieżkę odpowiedzi i zwracając błyskawiczne przekazane sterowania w trybie prompt.
- `Pamięć sesji (Kontekst)` – Skrypt w trakcie działania utrzymuje stałą "pamięć" całej dotychczasowej konwersacji (Twoje pytania, odczytane pliki oraz logi procesów z terminala). Pozwala to na płynne, naturalne rozwiązywanie problemów w wielu krokach, jednak pamięć ta jest ulotna i ulega całkowitemu zresetowaniu po wyłączeniu agenta (`exit`).

## ⚡ Interakcja powłokowa i Skrypty (Auto-DevOps)

Agent CLI domyślnie posiada włączone wsparcie dla bezpiecznego, natywnego egzekwowania komend shell/OS bez opuszczania interfejsu klienta.
Po zadaniu pytania konfiguracyjnego w luźnym formacie (np. *"sprawdź jakie porty kontenerów dockera są aktywne"* lub *"przekaż listę procesów dla pythona"*), model potrafi zwrócić precyzyjne polecenie obudowane tagiem `<execute>`.

Zastosowane mechanizmy nadzoru sprzętowego:
- Zanim interpreter prześle polecenie niżej, system **każdorazowo poprosi użytkownika o jawną zgodę** `(T/n)`, zapewniając 100% monitoringu nad egzekutorem.
- Moduł pozwala po przetworzonym żądaniu, przekazać wyrzut strumieni na podwójny tor. Decyzja `Y/N` wysyła odpowiedź `stdout` / `stderr` terminala z powrotem do podsieci powłoki agenta w celu dogłębnej analityki i streszczenia, bądź rzuca surowe logi operacji precyzyjnie prosto na widok powłoki. 
- Rozdzielona pętla redukuje do absolutnego zera zużycie tokenów i opóźnienia sprzętowe API dla znanych i pożądanych logów systemowych.
