import json
import urllib.request
import urllib.error
import socket
from config import PROVIDERS, MEMORY_WINDOW_LIMIT, MEMORY_SOFT_LIMIT, MAX_TOKENS, TEMPERATURE

# Maksymalny czas oczekiwania na odpowiedź API (w sekundach)
REQUEST_TIMEOUT = 30

class APIClient:
    def __init__(self, provider_name="cloudflare", providers_config=None):
        if providers_config is None:
            from config import PROVIDERS
            providers_config = PROVIDERS

        if provider_name not in providers_config:
            raise ValueError(f"Nieznany provider: {provider_name}")
            
        self.provider = provider_name
        self.config = providers_config[provider_name]
        self.url = self.config["url"]
        self.api_key = self.config["api_key"]
        self.model = self.config["default_model"]

    def set_model(self, model_name):
        self.model = model_name

    def estimate_tokens(self, messages):
        """Przybliżone liczenie tokenów (1 słowo ~= 1.33 tokena)."""
        text = ""
        for m in messages:
            text += m.get("content", "") + " "
        words = len(text.split())
        return int(words * 1.33)

    def chat_completion(self, messages):
        """Wysyła zapytanie do API wybranego providera."""
        # Obliczanie przybliżonej liczby tokenów w wysyłanych wiadomościach
        total_tokens = self.estimate_tokens(messages)
        
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "AI-DevOps-Agent/1.0"
        }

        # Obsługa specyficznych nagłówków dla różnych dostawców
        if self.provider == "anthropic":
            headers["x-api-key"] = self.api_key
            headers["anthropic-version"] = "2023-06-01"
        else:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        data = {
            "model": self.model,
            "messages": messages,
            "max_tokens": MAX_TOKENS,
            "temperature": TEMPERATURE
        }
        
        # Parametr reasoning tylko dla OpenRouter (modele reasoning jak nemotron)
        if self.provider == "openrouter":
            data["reasoning"] = {"effort": "low"}
        
        req = urllib.request.Request(
            self.url,
            data=json.dumps(data).encode("utf-8"),
            headers=headers,
            method="POST"
        )
        
        try:
            # Próba w pełni zabezpieczonego nawiązania połączenia szyfrowanego (domyślna dla np. Debiana)
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as response:
                result = json.loads(response.read().decode("utf-8"))
                # Użyj rzeczywistych tokenów z API jeśli dostępne, inaczej fallback na szacowanie
                actual_tokens = result.get("usage", {}).get("total_tokens", 0)
                if actual_tokens > 0:
                    result["_total_tokens"] = actual_tokens
                else:
                    result["_total_tokens"] = total_tokens  # fallback na szacowanie
                return result
                
        except socket.timeout:
            return {"error": f"Przekroczono limit czasu oczekiwania ({REQUEST_TIMEOUT}s). Sprawdź połączenie z internetem lub zwiększ REQUEST_TIMEOUT w client.py."}
                
        except urllib.error.HTTPError as e:
            # Kiedy występuje błąd HTTP (np. 401, 500) od strony serwera, po nawiązaniu TCP
            error_body = e.read().decode("utf-8")
            return {"error": f"Błąd HTTP {e.code}: {e.reason}\nSzczegóły: {error_body}"}
            
        except urllib.error.URLError as e:
            # Ten blok aktywuje się gdy system (np Mac) blokuje handshake przez certyfikaty
            if "CERTIFICATE_VERIFY_FAILED" in str(e.reason):
                from ui import Colors
                print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️ OSTRZEŻENIE: CERTIFICATE_VERIFY_FAILED{Colors.ENDC}")
                print(f"{Colors.YELLOW}Twój system zablokował dostęp ze względu na brak ważnych certyfikatów.{Colors.ENDC}")
                print(f"{Colors.YELLOW}Włączono ratunkowe obejście weryfikacji SSL! Z tego powodu Twoje połączenie{Colors.ENDC}")
                print(f"{Colors.YELLOW}od tej chwili nie jest weryfikowane, co oznacza potencjalną podatność{Colors.ENDC}")
                print(f"{Colors.YELLOW}na nasłuch w sieci publicznej (MITM). Zalecamy aktualizację systemu.{Colors.ENDC}\n")
                
                import ssl
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                try:
                    with urllib.request.urlopen(req, context=ctx, timeout=REQUEST_TIMEOUT) as response:
                        result = json.loads(response.read().decode("utf-8"))
                        actual_tokens = result.get("usage", {}).get("total_tokens", 0)
                        if actual_tokens > 0:
                            result["_total_tokens"] = actual_tokens
                        else:
                            result["_total_tokens"] = total_tokens
                        return result
                except socket.timeout:
                    return {"error": f"Przekroczono limit czasu oczekiwania ({REQUEST_TIMEOUT}s). Sprawdź połączenie lub zwiększ REQUEST_TIMEOUT w client.py."}
                except urllib.error.HTTPError as he:
                    return {"error": f"Błąd HTTP {he.code}: {he.reason}\nSzczegóły: {he.read().decode('utf-8')}"}
                except Exception as inner_e:
                    return {"error": str(inner_e)}
            return {"error": str(e)}
        except Exception as e:
            return {"error": str(e)}
