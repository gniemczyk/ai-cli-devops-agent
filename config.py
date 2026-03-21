import os

# ==============================================================================
# 1. KONFIGURACJA UŻYTKOWNIKA (Tu możesz wprowadzać zmiany)
# ==============================================================================

# Domyślny dostawca API (wybierz: "cloudflare", "openai", "anthropic", "gemini")
DEFAULT_PROVIDER = "cloudflare"

# Domyślny model AI
DEFAULT_MODEL = "workers-ai/@cf/meta/llama-4-scout-17b-16e-instruct"

# Adres Cloudflare AI Gateway (podmień jeśli Cloudflare zmieni strukturę endpointu)
# Numer konta ({CF_NR_ACCOOUNT}) wczytywany jest automatycznie z pliku .env
CF_GATEWAY_URL_TEMPLATE = "https://gateway.ai.cloudflare.com/v1/{account}/ai-gateway-model-ai/compat"


# ==============================================================================
# 2. LOGIKA WEWNĘTRZNA (Zaleca się nie zmieniać poniższego)
# ==============================================================================

def load_env(filepath=".env"):
    """Ładuje zmienne środowiskowe z pliku tekstowego (bez zewnętrznych bibliotek)."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip().strip("'\"")
                    if key not in os.environ:
                        os.environ[key] = val
    except FileNotFoundError:
        pass

# Wczytywanie z pliku ukrytego .env w głównym katalogu obok pliku config
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_env(os.path.join(BASE_DIR, ".env"))

# Pobranie wrażliwych danych z środowiska
CF_API_TOKEN   = os.environ.get("CF_API_TOKEN", "")
CF_NR_ACCOOUNT = os.environ.get("CF_NR_ACCOOUNT", "")

# Budowanie pełnego adresu Cloudflare Gateway
CF_GATEWAY_URL = CF_GATEWAY_URL_TEMPLATE.format(account=CF_NR_ACCOOUNT)

# Słownik dostawców
PROVIDERS = {
    "cloudflare": {
        "url": f"{CF_GATEWAY_URL}/chat/completions",
        "api_key": CF_API_TOKEN,
        "default_model": DEFAULT_MODEL
    },
    "openai": {
        "url": "https://api.openai.com/v1/chat/completions",
        "api_key": os.environ.get("OPENAI_API_KEY", ""),
        "default_model": "gpt-4o"
    },
    "anthropic": {
        "url": "https://api.anthropic.com/v1/messages",
        "api_key": os.environ.get("ANTHROPIC_API_KEY", ""),
        "default_model": "claude-3-5-sonnet-20241022"
    },
    "gemini": {
        "url": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        "api_key": os.environ.get("GEMINI_API_KEY", ""),
        "default_model": "gemini-2.0-flash"
    },
}
