import os
import sys
from config import DEFAULT_PROVIDER, PROVIDERS

def load_env(filepath=".env"):
    """Ładuje zmienne środowiskowe z pliku tekstowego (bez zewnętrznych bibliotek)."""
    try:
        # Znajdź .env w katalogu głównym projektu
        base_dir = os.path.dirname(os.path.abspath(__file__))
        env_path = os.path.join(base_dir, filepath)
        
        if not os.path.exists(env_path):
            return

        with open(env_path, "r", encoding="utf-8") as f:
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
    except Exception:
        pass

def validate_and_setup():
    """Wczytuje .env, waliduje klucze i zwraca skonfigurowany słownik PROVIDERS."""
    load_env()
    
    # Kopia, żeby nie modyfikować oryginału w config.py (choć i tak go nadpiszemy w locie)
    active_providers = PROVIDERS.copy()
    
    # Pobranie danych z środowiska
    cf_token = os.environ.get("CF_API_TOKEN", "")
    cf_account = os.environ.get("CF_NR_ACCOUNT", "")

    # Aktualizacja kluczy i adresów
    for p_name, p_config in active_providers.items():
        if p_name == "cloudflare":
            p_config["api_key"] = cf_token
            if "{account}" in p_config["url"]:
                p_config["url"] = p_config["url"].format(account=cf_account)
        else:
            env_key = f"{p_name.upper()}_API_KEY"
            if os.environ.get(env_key):
                p_config["api_key"] = os.environ.get(env_key)

    # Walidacja wybranego providera
    if DEFAULT_PROVIDER == "cloudflare":
        missing = []
        if not os.environ.get("CF_API_TOKEN"):
            missing.append("CF_API_TOKEN")
        if not os.environ.get("CF_NR_ACCOUNT"):
            missing.append("CF_NR_ACCOUNT")
        if missing:
            raise ValueError(f"Brak wymaganych zmiennych w .env dla Cloudflare: {', '.join(missing)}")
    else:
        env_key = f"{DEFAULT_PROVIDER.upper()}_API_KEY"
        if not os.environ.get(env_key):
            raise ValueError(f"Brak {env_key} w .env dla providera {DEFAULT_PROVIDER}")
            
    return active_providers
