import os

# ==============================================================================
# 1. KONFIGURACJA UŻYTKOWNIKA (Tu wprowadzaj swoje zmiany)
# ==============================================================================

# Domyślny dostawca API (wybierz: "cloudflare", "openai", "anthropic", "gemini", "openrouter")
DEFAULT_PROVIDER = "cloudflare"

# Domyślny model AI (używany dla wszystkich dostawców)
DEFAULT_MODEL = "workers-ai/@cf/google/gemma-4-26b-a4b-it"

# Progi i limity pamięci (Tokeny)
# Przybliżona liczba tokenów (1 słowo ~= 1.33 tokena)
MEMORY_WINDOW_LIMIT = 2000  # Maksymalna liczba tokenów w pamięci zanim zaczniemy ostrzegać
MEMORY_SOFT_LIMIT = 3000    # Próg po którym pojawia się ostrzeżenie o dużej ilości danych

# Limity tokenów dla odpowiedzi API
MAX_TOKENS = 4096           # Maksymalna liczba tokenów w odpowiedzi modelu
TEMPERATURE = 0.2           # Temperatura modelu (0.0-1.0, niższa = bardziej zwięzłe odpowiedzi)

# Słownik dostawców
# Możesz tutaj dodawać własnych dostawców zgodnych z OpenAI API
PROVIDERS = {
    "cloudflare": {
        "url": "https://gateway.ai.cloudflare.com/v1/{account}/ai-gateway-model-ai/compat/chat/completions",
        "api_key": "", # Wypełniane automatycznie z .env przez env_loader.py
        "default_model": DEFAULT_MODEL,
    },
    "openai": {
        "url": "https://api.openai.com/v1/chat/completions",
        "api_key": "", # Wypełniane automatycznie z .env
        "default_model": DEFAULT_MODEL
    },
    "anthropic": {
        "url": "https://api.anthropic.com/v1/messages",
        "api_key": "", # Wypełniane automatycznie z .env
        "default_model": DEFAULT_MODEL
    },
    "gemini": {
        "url": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        "api_key": "", # Wypełniane automatycznie z .env
        "default_model": DEFAULT_MODEL
    },
    "openrouter": {
        "url": "https://openrouter.ai/api/v1/chat/completions",
        "api_key": "", # Wypełniane automatycznie z OPENROUTER_API_KEY w .env
        "default_model": DEFAULT_MODEL
    },
}
