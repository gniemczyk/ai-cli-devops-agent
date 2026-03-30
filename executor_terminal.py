"""
Moduł obsługi terminala - resetowanie stanu terminala po komendach.
"""
import sys
import subprocess

try:
    import termios
    import tty
    UNIX_AVAILABLE = True
except ImportError:
    UNIX_AVAILABLE = False  # Windows


def reset_terminal_state():
    """Resetuje stan terminala dla uniknięcia blokowania na Linux."""
    if not UNIX_AVAILABLE:
        return  # Windows nie potrzebuje resetu terminala
    
    try:
        # Przywróć ustawienia terminala
        if hasattr(sys.stdin, 'fileno'):
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            # Dodatkowo wymuś tryb kanoniczny
            new_settings = termios.tcgetattr(fd)
            new_settings[3] = new_settings[3] | termios.ICANON | termios.ECHO
            termios.tcsetattr(fd, termios.TCSADRAIN, new_settings)
    except:
        pass  # Ignoruj błędy na macOS/Windows
    
    # Ostateczność - uruchom stty sane (tylko Unix)
    try:
        subprocess.run(['stty', 'sane'], stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr, timeout=1)
    except:
        pass
