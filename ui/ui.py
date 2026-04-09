class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_system(msg):
    print(f"{Colors.YELLOW}⚡ {msg}{Colors.ENDC}")

def print_error(msg):
    print(f"{Colors.RED}❌ BŁĄD: {msg}{Colors.ENDC}")
