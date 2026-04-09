# AI CLI DevOps Agent

Lekki agent CLI w Pythonie (bez pip) do bezpiecznej komunikacji z modelami LLM. Domyślnie: Cloudflare AI Gateway.

> 💡 **Darmowy limit:** Cloudflare AI oferuje **10k Neurons dziennie** na darmowym koncie. Po wyczerpaniu API zwraca błąd limitu (bez dodatkowych opłat).

## 🛠 Struktura

```
/
├── agent.py              # Główny plik wejściowy (koordynacja modułów)
├── config.py             # Konfiguracja providera/modelu
├── core/                 # Moduły podstawowe
│   ├── client.py         # Klient HTTP (urllib) dla OpenAI API
│   ├── conversation.py   # Zarządzanie konwersacją i historią
│   └── response_handler.py  # Obsługa odpowiedzi od API
├── ui/                   # Interfejs użytkownika
│   ├── ui.py             # Kolory i formatowanie terminala
│   └── cli.py            # Obsługa interfejsu wiersza poleceń
├── utils/                # Narzędzia
│   ├── env_loader.py     # Ładowanie `.env` i walidacja
│   ├── file_utils.py     # Obsługa `@plik` i komend `@`
│   └── compact.py        # Kompresja historii (auto-podsumowania)
├── executor/             # Silnik wykonywania komend
│   ├── executor.py       # Główny agregator
│   ├── executor_runner.py   # Główna logika wykonywania
│   ├── executor_security.py # Sprawdzanie bezpieczeństwa
│   ├── executor_output.py    # Obsługa dużych danych wyjściowych
│   └── executor_terminal.py  # Resetowanie stanu terminala
└── skills/               # Formatowanie odpowiedzi
    └── skills.py         # System formatowania odpowiedzi
```

## 🎨 Skille Formatowania

Agent automatycznie stylizuje odpowiedzi używając:
- **Emotek statusów:** ✅ OK, ❌ Błąd, ⚠️ Warning, 🔥 High CPU, 💾 High RAM, 🔌 Port, ⏳ Timeout
- **Struktury:** nagłówki `###`, listy `-`, `**pogrubienie**`, `kod`
- **Brak tabel** w terminalu (używamy kompaktowych list)

## 🚀 Instalacja

```bash
# 1. Skopiuj .env.example do .env i wypełnij
cp .env.example .env

# 2. Uruchom
python3 agent.py
```

## 🔌 Dostawcy

| Dostawca | `config.py` | Klucz `.env` | Model domyślny |
|----------|-------------|--------------|----------------|
| Cloudflare AI (domyślny) | `"cloudflare"` | `CF_API_TOKEN` + `CF_NR_ACCOUNT` | llama-4-scout |
| OpenAI | `"openai"` | `OPENAI_API_KEY` | gpt-4o |
| Anthropic | `"anthropic"` | `ANTHROPIC_API_KEY` | claude-3-5-sonnet |
| Google Gemini | `"gemini"` | `GEMINI_API_KEY` | gemini-2.0-flash |
| OpenRouter | `"openrouter"` | `OPENROUTER_API_KEY` | zależny |

## ⌨️ Funkcje

- `@plik` – wczytaj plik do kontekstu (walidacja ścieżki, limit 1MB)
- `@clear` – wyczyść pamięć agenta
- `@compact` – skompresuj historię (podsumowania zamiast surowych wiadomości, oszczędza tokeny)
- `?` – wyjaśnij komendę przed wykonaniem
- `n` – odmowa wykonania (błyskawiczna)
- Licznik tokenów: `🤖 Agent (1240t)`
- Ostrzeżenie o dużej pamięci (próg w `config.py`)
- **Auto-kompresja** – automatyczne podsumowywanie historii przy zbliżaniu się do limitu tokenów

## ⚡ Auto-DevOps

Agent może wykonywać komendy systemowe przez `<execute>komenda</execute>`:
- **Autoryzacja:** każdorazowe pytanie `(T/n/?)`
- **Duże wyjście:** opcje T/P/O/N/S (przycięcie, pierwsze/ostatnie 50 linii, zapis do pliku)
- **Timeout:** 10s limit na komendę
- **Bezpieczeństwo:** sprawdzanie niebezpiecznych komend i ścieżek

## 🔧 SSL (jeśli wymagane)

**macOS:**
```bash
open "/Applications/Python "*"/Install Certificates.command"
```

**Linux:**
```bash
sudo apt update && sudo apt install ca-certificates
```

---

**Autor:** Grzegorz N  
**Data:** Marzec 2026