"""
Moduł executor - główny agregujący wszystkie komponenty wykonywania komend.

Ten moduł jest backward-compatible - eksportuje handle_agent_commands i reset_terminal_state
które były używane przez agent.py i inne moduły.

Struktura modułów:
- executor_terminal.py - resetowanie stanu terminala
- executor_security.py - sprawdzanie bezpieczeństwa komend
- executor_output.py - obsługa wyjścia i dużych danych
- executor_runner.py - główna logika wykonywania komend
"""

# Backward compatibility - eksportujemy główne funkcje
from executor.executor_terminal import reset_terminal_state
from executor.executor_runner import handle_agent_commands

__all__ = ['handle_agent_commands', 'reset_terminal_state']
