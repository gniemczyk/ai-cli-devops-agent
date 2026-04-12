"""
Moduł bezpieczeństwa - sprawdzanie czy komenda jest niebezpieczna.
"""
import re


def is_dangerous_command(cmd):
    """Sprawdza czy komenda odnosi się do ścieżek/operacji uznanych za groźne."""
    # Ścieżki systemowe (bez ~ - to katalog domowy użytkownika)
    dangerous_paths = [
        '/etc', '/usr', '/bin', '/sbin', '/var', '/proc', '/sys', '/dev', '/root'
    ]
    
    cmd_lower = cmd.lower()
    
    # Sprawdź path traversal - tylko gdy .. jest osobnym tokenem (ścieżka lub argument)
    # Wyklucza false positive dla np. "echo '...'" (trzy kropki) lub "git log --oneline"
    if re.search(r'(?:^|\s|/|\'|")\.\.(?:$|/|\s|\'|")', cmd):
        return True
        
    for path in dangerous_paths:
        # Sprawdzamy czy ścieżka występuje jako osobny "token" lub początek ścieżki
        # tzn. poprzedzona spacją lub będąca na początku, i zakończona spacją, slashem lub końcem linii
        pattern = rf"(^|\s){re.escape(path)}($|[\s/])"
        if re.search(pattern, cmd_lower):
            return True
            
    # Rozszerzona lista niebezpiecznych komend
    dangerous_commands = [
        # Modyfikatory plików/systemu
        'rm ', 'chmod ', 'chown ', 'dd', 'mkfs', 'fdisk', 'parted',
        # Zarządzanie systemem
        'shutdown', 'reboot', 'halt', 'poweroff', 'systemctl',
        # Procesy
        'kill ', 'pkill', 'killall',
        # Eksfiltracja danych / sieci
        'curl ', 'wget ', 'nc ', 'netcat', 'scp ', 'rsync',
        # Wykonywanie kodu / injection
        'python', 'python3', 'perl ', 'ruby ', 'node ', 'php ',
        'eval ', 'exec ', 'source ',
        # Uprawnienia
        'sudo ', 'su ', 'doas ',
        # Sieć/firewall
        'iptables', 'firewall-cmd', 'ufw',
        # Automatyzacja/zadania
        'crontab', 'at ',
        # Zarządzanie użytkownikami
        'useradd', 'userdel', 'usermod', 'passwd',
        # Inne niebezpieczne
        'mv /', 'cp /', 'cat /etc/', 'vim /etc/', 'nano /etc/',
        '>', '>>', '|', '&&', '||',  # przekierowania i łańcuchy komend
    ]
    
    for dangerous in dangerous_commands:
        # Zabezpieczenie przed substringami (np. 'at' w 'cat')
        # Używamy regex, aby sprawdzić czy komenda występuje jako osobny token
        # Wyjątek dla operatorów przekierowań i potoków - sprawdzamy poza cudzysłowami
        if dangerous in ['>', '>>', '|', '&&', '||']:
            # Usuń zawartość cudzysłowów przed sprawdzeniem
            cmd_no_quotes = re.sub(r'"[^"]*"', '', cmd_lower)
            cmd_no_quotes = re.sub(r"'[^']*'", '', cmd_no_quotes)
            if dangerous in cmd_no_quotes:
                return True
            continue
            
        # Sprawdzamy czy fraza występuje na początku lub po spacji, 
        # oraz kończy się spacją, slashem lub końcem linii
        # Przycinamy 'dangerous' z białych znaków, bo regex sam obsłuży granice
        clean_dangerous = dangerous.strip()
        pattern = rf"(^|\s){re.escape(clean_dangerous)}($|[\s/])"
        if re.search(pattern, cmd_lower):
            return True
        
    return False
