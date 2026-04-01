"""
compact.py - Moduł kompresji historii konwersacji.

Automatycznie kompresuje długie historie wiadomości gdy zbliżają się do limitu tokenów.
Zastępuje surową historię spójnymi podsumowaniami, oszczędzając tokeny.
"""

import re
from typing import List, Dict, Any, Tuple
from ui import Colors, print_system


def estimate_tokens(text: str) -> int:
    """
    Bardziej dokładne szacowanie tokenów dla modeli LLM.
    
    Heurystyka:
    - Tekst angielski: ~4 znaki na token
    - Kod/techniczny: ~3 znaki na token (więcej symboli)
    - Spacje/newlines: osobne tokeny
    - Unicode/non-ASCII: często 2-3 tokeny na znak
    """
    if not text:
        return 0
    
    # Zliczaj znaki
    total_chars = len(text)
    
    # Zliczaj znaki specjalne (kod techniczny)
    special_chars = sum(1 for c in text if c in '[]{}()<>/\\|=-+*&^%$#@!;:\'"`')
    
    # Zliczaj whitespace (każdy to potencjalnie token)
    whitespace = sum(1 for c in text if c in ' \t\n')
    
    # Zliczaj non-ASCII
    non_ascii = sum(1 for c in text if ord(c) > 127)
    
    # Algorytm wagowy
    # Baza: ~3.5 znaku na token dla tekstu technicznego
    base_estimate = total_chars / 3.5
    
    # Korekty
    special_boost = special_chars * 0.3  # Symbole często osobne tokeny
    whitespace_boost = whitespace * 0.2    # Whitespace to tokeny
    non_ascii_boost = non_ascii * 1.0    # Non-ASCII = więcej tokenów
    
    estimated = base_estimate + special_boost + whitespace_boost + non_ascii_boost
    
    # Dodaj padding dla systemu formatowania/markdown
    estimated *= 1.1
    
    return int(estimated)


def count_messages_tokens(messages: List[Dict[str, Any]]) -> int:
    """Liczy tokeny w liście wiadomości."""
    total = 0
    for m in messages:
        total += estimate_tokens(m.get("content", ""))
    return total


def extract_command_from_message(content: str) -> str:
    """Wyciąga komendę z execute tagów."""
    match = re.search(r'<execute>(.*?)</execute>', content, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return ""


def summarize_exchange(
    user_msg: Dict[str, Any],
    assistant_msg: Dict[str, Any],
    client=None
) -> str:
    """
    Tworzy podsumowanie pary user-assistant.
    Jeśli client jest dostępny, używa AI do podsumowania.
    W przeciwnym razie używa prostego heurystycznego podsumowania.
    """
    user_content = user_msg.get("content", "")
    assistant_content = assistant_msg.get("content", "")
    
    # Sprawdź czy była komenda wykonana
    cmd = extract_command_from_message(assistant_content)
    
    # Proste heurystyczne podsumowanie (fallback bez AI)
    if cmd:
        # Wyodrębnij kluczowe informacje z wyniku komendy
        cmd_preview = cmd[:50] + "..." if len(cmd) > 50 else cmd
        return f"Wykonano: `{cmd_preview}` - komenda systemowa"
    
    # Podsumowanie pytania i odpowiedzi
    user_preview = user_content[:60].replace('\n', ' ')
    if len(user_content) > 60:
        user_preview += "..."
    
    # Sprawdź czy odpowiedź zawiera błąd
    has_error = any(indicator in assistant_content.lower() 
                   for indicator in ['błąd', 'error', 'nie udało', 'failed', '❌'])
    
    status = " (wystąpił błąd)" if has_error else ""
    
    return f"Zapytanie: {user_preview}{status}"


def compress_messages(
    messages: List[Dict[str, Any]],
    target_tokens: int,
    client=None
) -> Tuple[List[Dict[str, Any]], int, int]:
    """
    Kompresuje historię wiadomości do target_tokens.
    
    Returns:
        Tuple: (skompresowane wiadomości, liczba przed, liczba po)
    """
    if len(messages) <= 2:  # System message + co najmniej 1 para
        return messages, len(messages), len(messages)
    
    original_count = len(messages)
    original_tokens = count_messages_tokens(messages)
    
    # Zachowaj system message
    system_msg = messages[0] if messages[0].get("role") == "system" else None
    
    # Reszta wiadomości (user/assistant pary)
    conversation = [m for m in messages if m.get("role") != "system"]
    
    # Podziel na pary user-assistant
    pairs = []
    for i in range(0, len(conversation) - 1, 2):
        if conversation[i].get("role") == "user" and i + 1 < len(conversation):
            pairs.append((conversation[i], conversation[i + 1]))
    
    if not pairs:
        return messages, original_count, original_count
    
    # Zdecyduj ile par zachować w pełnej formie (ostatnie pary)
    # Zawsze zachowaj ostatnie 2 pary w oryginalnej formie dla kontekstu
    keep_full = min(2, len(pairs))
    pairs_to_summarize = pairs[:-keep_full] if keep_full > 0 else pairs
    recent_pairs = pairs[-keep_full:] if keep_full > 0 else []
    
    # Podsumuj starsze pary
    summaries = []
    for user_msg, assistant_msg in pairs_to_summarize:
        summary = summarize_exchange(user_msg, assistant_msg, client)
        summaries.append(summary)
    
    # Zbuduj nową listę wiadomości
    compressed = []
    if system_msg:
        compressed.append(system_msg)
    
    # Dodaj podsumowanie jako jedna wiadomość systemowa
    if summaries:
        summary_text = "📋 Podsumowanie wcześniejszej konwersacji:\n" + "\n".join(
            f"{i+1}. {s}" for i, s in enumerate(summaries[-10:])  # Max 10 podsumowań
        )
        compressed.append({
            "role": "system",
            "content": summary_text,
            "_is_compression_summary": True
        })
    
    # Dodaj ostatnie pary w pełnej formie
    for user_msg, assistant_msg in recent_pairs:
        compressed.append(user_msg)
        compressed.append(assistant_msg)
    
    # Jeśli została nieparzysta wiadomość (np. ostatnia bez odpowiedzi)
    if len(conversation) % 2 == 1:
        compressed.append(conversation[-1])
    
    new_count = len(compressed)
    new_tokens = count_messages_tokens(compressed)
    
    return compressed, original_count, new_count


def should_compress(
    messages: List[Dict[str, Any]],
    soft_limit: int,
    window_limit: int
) -> bool:
    """Sprawdza czy należy skompresować historię."""
    if len(messages) < 4:  # Minimum: system + 1 para + coś jeszcze
        return False
    
    tokens = count_messages_tokens(messages)
    return tokens >= soft_limit


def format_compression_stats(
    original_count: int,
    new_count: int,
    original_tokens: int,
    new_tokens: int
) -> str:
    """Formatuje statystyki kompresji."""
    saved_msgs = original_count - new_count
    saved_tokens = original_tokens - new_tokens
    
    return (
        f"🗜️  Skrócono {original_count} → {new_count} wiadomości "
        f"({saved_msgs} zaoszczędzonych, {saved_tokens}t mniej)"
    )


def compress_if_needed(
    messages: List[Dict[str, Any]],
    soft_limit: int,
    window_limit: int,
    client=None,
    verbose: bool = True
) -> List[Dict[str, Any]]:
    """
    Sprawdza czy kompresja jest potrzebna i wykonuje ją.
    
    Args:
        messages: Lista wiadomości
        soft_limit: Próg ostrzeżenia (kompresuj gdy przekroczony)
        window_limit: Maksymalny limit (kompresuj agresywnie gdy blisko)
        client: Klient API do AI podsumowań (opcjonalnie)
        verbose: Czy wyświetlać informacje o kompresji
    
    Returns:
        Skompresowana lub oryginalna lista wiadomości
    """
    if not should_compress(messages, soft_limit, window_limit):
        return messages
    
    current_tokens = count_messages_tokens(messages)
    
    if verbose:
        print_system(
            f"⚠️  Pamięć: {current_tokens} tokenów. Kompresja historii..."
        )
    
    # Agresywniejsza kompresja gdy bliżej hard limit
    target = window_limit * 0.6 if current_tokens > window_limit * 0.9 else window_limit * 0.7
    
    compressed, orig_count, new_count = compress_messages(messages, int(target), client)
    
    new_tokens = count_messages_tokens(compressed)
    
    if verbose:
        stats = format_compression_stats(orig_count, new_count, current_tokens, new_tokens)
        print_system(f"🗜️  {stats}")
    
    return compressed
