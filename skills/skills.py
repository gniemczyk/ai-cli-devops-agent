"""
Skills module - predefiniowane umiejętności formatowania dla Agenta DevOps.

Ten moduł dostarcza funkcje formatujące różne typy danych wyjściowych,
aby Agent prezentował wyniki w czytelny i profesjonalny sposób.
"""

from typing import List, Dict, Any, Optional


class FormatSkill:
    """Bazowa klasa dla skilli formatujących."""
    
    @staticmethod
    def header(text: str, level: int = 2) -> str:
        """Generuje nagłówek markdown."""
        return f"{'#' * level} {text}"
    
    @staticmethod
    def bold(text: str) -> str:
        """Pogrubia tekst."""
        return f"**{text}**"
    
    @staticmethod
    def code(text: str, language: str = "") -> str:
        """Tworzy blok kodu."""
        if language:
            return f"```{language}\n{text}\n```"
        return f"`{text}`"
    
    @staticmethod
    def bullet(items: List[str], indent: int = 0) -> str:
        """Tworzy listę wypunktowaną."""
        prefix = "  " * indent + "- "
        return "\n".join(f"{prefix}{item}" for item in items)
    
    @staticmethod
    def number(items: List[str]) -> str:
        """Tworzy listę numerowaną."""
        return "\n".join(f"{i+1}. {item}" for i, item in enumerate(items))
    
    @staticmethod
    def status_emoji(status: str) -> str:
        """Zwraca emotkę statusu."""
        emojis = {
            "ok": "✅",
            "success": "✅",
            "error": "❌",
            "fail": "❌",
            "warning": "⚠️",
            "warn": "⚠️",
            "info": "ℹ️",
            "pending": "⏳",
            "running": "🔄",
            "stopped": "🛑",
        }
        return emojis.get(status.lower(), "•")


class DockerSkill(FormatSkill):
    """Skill do formatowania wyjścia Docker."""
    
    @classmethod
    def format_ps(cls, containers: List[Dict[str, Any]]) -> str:
        """Formatuje listę kontenerów docker ps."""
        lines = [cls.header("Kontenery Docker", 3)]
        
        if not containers:
            lines.append(f"{cls.status_emoji('info')} Brak uruchomionych kontenerów")
            return "\n".join(lines)
        
        for c in containers:
            status = c.get("Status", "").lower()
            emoji = cls.status_emoji("ok" if "up" in status else "error")
            
            lines.append(f"\n{emoji} **{c.get('Names', 'N/A')}** (`{c.get('ID', 'N/A')[:12]}`)")
            lines.append(f"  - Obraz: `{c.get('Image', 'N/A')}`")
            lines.append(f"  - Status: {c.get('Status', 'N/A')}")
            lines.append(f"  - Porty: {c.get('Ports', 'brak')}")
        
        return "\n".join(lines)
    
    @classmethod
    def format_logs(cls, logs: str, container_name: str) -> str:
        """Formatuje logi kontenera."""
        lines = [
            cls.header(f"Logi: {container_name}", 3),
            "",
            cls.code(logs, "log"),
        ]
        return "\n".join(lines)
    
    @classmethod
    def format_system_df(cls, data: Dict[str, Any]) -> str:
        """Formatuje wyjście docker system df."""
        lines = [cls.header("Użycie przestrzeni Docker", 3), ""]
        
        for item_type, items in data.items():
            total = sum(i.get("Size", 0) for i in items)
            lines.append(f"**{item_type.capitalize()}:** {len(items)} obiektów ({cls._human_size(total)})")
        
        return "\n".join(lines)
    
    @staticmethod
    def _human_size(size_bytes: int) -> str:
        """Konwertuje bajty na czytelną formę."""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} PB"


class SystemSkill(FormatSkill):
    """Skill do formatowania informacji systemowych."""
    
    @classmethod
    def format_processes(cls, processes: List[Dict[str, str]]) -> str:
        """Formatuje listę procesów (ps aux)."""
        lines = [cls.header("Procesy systemowe", 3)]
        
        if len(processes) > 10:
            lines.append(f"{cls.status_emoji('info')} Wyświetlono 10/{len(processes)} procesów")
            processes = processes[:10]
        
        for p in processes:
            cpu = float(p.get("%CPU", 0))
            mem = float(p.get("%MEM", 0))
            
            # Emotki dla wysokiego zużycia
            cpu_emoji = "🔥" if cpu > 50 else ""
            mem_emoji = "💾" if mem > 30 else ""
            
            lines.append(f"- **{p.get('COMMAND', 'N/A')}** (PID: `{p.get('PID', 'N/A')}`)")
            lines.append(f"  CPU: {cpu}% {cpu_emoji} | MEM: {mem}% {mem_emoji} | USER: {p.get('USER', 'N/A')}")
        
        return "\n".join(lines)
    
    @classmethod
    def format_disk_usage(cls, mounts: List[Dict[str, str]]) -> str:
        """Formatuje użycie dysku (df -h)."""
        lines = [cls.header("Użycie dysku", 3), ""]
        
        for m in mounts:
            used_pct = m.get("Use%", "0%").replace("%", "")
            try:
                pct = int(used_pct)
                emoji = cls.status_emoji("error" if pct > 90 else "warning" if pct > 70 else "ok")
            except:
                emoji = cls.status_emoji("info")
            
            lines.append(f"{emoji} `{m.get('Mounted on', 'N/A')}` - {m.get('Used', 'N/A')}/{m.get('Size', 'N/A')} ({m.get('Use%', 'N/A')})")
        
        return "\n".join(lines)
    
    @classmethod
    def format_service_status(cls, service: str, status: str, logs: Optional[str] = None) -> str:
        """Formatuje status usługi systemowej."""
        is_active = "active" in status.lower() or "running" in status.lower()
        emoji = cls.status_emoji("ok" if is_active else "error")
        
        lines = [
            f"{emoji} **{service}** - {status}",
        ]
        
        if logs and not is_active:
            lines.append("")
            lines.append(cls.code(logs[-1000:], "log"))  # Ostatnie 1000 znaków logów
        
        return "\n".join(lines)


class AnalysisSkill(FormatSkill):
    """Skill do formatowania analiz i raportów."""
    
    @classmethod
    def format_analysis(cls, title: str, summary: str, sections: Dict[str, Any]) -> str:
        """Formatuje pełną analizę z sekcjami."""
        lines = [
            cls.header(title, 2),
            "",
            cls.bold("Podsumowanie:") + f" {summary}",
            "",
        ]
        
        for section_name, content in sections.items():
            lines.append(cls.header(section_name, 3))
            
            if isinstance(content, list):
                lines.append(cls.bullet(content))
            elif isinstance(content, dict):
                for key, value in content.items():
                    lines.append(f"- **{key}:** {value}")
            else:
                lines.append(str(content))
            
            lines.append("")
        
        return "\n".join(lines)
    
    @classmethod
    def format_error_analysis(cls, error_msg: str, context: str = "") -> str:
        """Formatuje analizę błędu."""
        lines = [
            f"{cls.status_emoji('error')} {cls.bold('Wykryto błąd')}",
            "",
            cls.code(error_msg, "error"),
        ]
        
        if context:
            lines.extend(["", cls.bold("Kontekst:"), context])
        
        return "\n".join(lines)
    
    @classmethod
    def format_recommendations(cls, items: List[str]) -> str:
        """Formatuje listę rekomendacji."""
        lines = [
            cls.header("Rekomendacje", 3),
            "",
        ]
        
        for i, item in enumerate(items, 1):
            lines.append(f"{i}. {item}")
        
        return "\n".join(lines)
    
    @classmethod
    def format_diff(cls, file_path: str, old: str, new: str) -> str:
        """Formatuje porównanie zmian (diff)."""
        lines = [
            cls.header(f"Zmiany w {file_path}", 3),
            "",
            "```diff",
        ]
        
        old_lines = old.splitlines()
        new_lines = new.splitlines()
        
        # Prosty diff
        for line in old_lines:
            if line not in new_lines:
                lines.append(f"- {line}")
        
        for line in new_lines:
            if line not in old_lines:
                lines.append(f"+ {line}")
        
        lines.append("```")
        
        return "\n".join(lines)


class NetworkSkill(FormatSkill):
    """Skill do formatowania informacji sieciowych."""
    
    @classmethod
    def format_ports(cls, ports: List[Dict[str, Any]]) -> str:
        """Formatuje otwarte porty (netstat/ss)."""
        lines = [cls.header("Otwarte porty", 3), ""]
        
        for p in ports:
            state = p.get("State", "UNKNOWN")
            emoji = {
                "LISTEN": "🔌",
                "ESTABLISHED": "✅",
                "TIME_WAIT": "⏳",
                "CLOSE_WAIT": "🚪",
            }.get(state, "•")
            
            lines.append(f"{emoji} `{p.get('Local Address', 'N/A')}` -> `{p.get('Foreign Address', 'N/A')}` ({state})")
            if p.get('Process'):
                lines.append(f"   Proces: {p.get('Process')}")
        
        return "\n".join(lines)
    
    @classmethod
    def format_ping(cls, host: str, stats: Dict[str, Any]) -> str:
        """Formatuje wyniki ping."""
        success = stats.get("packet_loss", 100) < 100
        emoji = cls.status_emoji("ok" if success else "error")
        
        return f"{emoji} **{host}** - RTT: {stats.get('avg_rtt', 'N/A')}ms, Loss: {stats.get('packet_loss', 'N/A')}%"


# Funkcje pomocnicze do parsowania wyjścia komend

def parse_docker_ps(output: str) -> List[Dict[str, str]]:
    """Parsuje wyjście docker ps do listy słowników."""
    lines = output.strip().splitlines()
    if not lines:
        return []
    
    # Nagłówki
    headers = lines[0].split()
    containers = []
    
    for line in lines[1:]:
        parts = line.split(None, len(headers) - 1)
        if len(parts) >= len(headers):
            container = dict(zip(headers, parts))
            containers.append(container)
    
    return containers


def parse_ps_aux(output: str) -> List[Dict[str, str]]:
    """Parsuje wyjście ps aux."""
    lines = output.strip().splitlines()
    if len(lines) < 2:
        return []
    
    # ps aux ma stałe kolumny: USER PID %CPU %MEM VSZ RSS TTY STAT START TIME COMMAND
    headers = ["USER", "PID", "%CPU", "%MEM", "VSZ", "RSS", "TTY", "STAT", "START", "TIME", "COMMAND"]
    processes = []
    
    for line in lines[1:]:
        parts = line.split(None, 10)  # COMMAND może zawierać spacje
        if len(parts) >= len(headers):
            processes.append(dict(zip(headers, parts)))
    
    return processes


def parse_df(output: str) -> List[Dict[str, str]]:
    """Parsuje wyjście df -h."""
    lines = output.strip().splitlines()
    if not lines:
        return []
    
    # Nagłówki
    headers = lines[0].split()
    mounts = []
    
    for line in lines[1:]:
        parts = line.split()
        if len(parts) >= len(headers):
            mounts.append(dict(zip(headers, parts)))
    
    return mounts


# Główna funkcja exportowana do agent.py
def get_system_prompt_addon() -> str:
    """
    Zwraca dodatek do system prompt z instrukcjami formatowania.
    Agent powinien dodać ten tekst do swojego system message.
    """
    return """
## SKILLE FORMATOWANIA

Używaj poniższych konwencji przy odpowiadaniu:

### WAŻNE - Format dla terminala:
- **NIE używaj komendy `cd`** bez łączenia jej z inną komendą (np. `cd folder && polecenie`), ponieważ każda Twoja komenda uruchamiana jest w osobnym podprocesie i samo `cd` nie zadziała na kolejne polecenia!
- **NIE używaj tabel** (| kolumna |) - w terminalu są nieczytelne!
- Używaj **kompaktowych list** z wypunktowaniem lub numeracją
- Maksymalnie 2-3 poziomy zagłębienia (nagłówek → punkt → podpunkt)
- Jedna linia = jedna informacja
- Używaj emotek do szybkiej identyfikacji typu elementu

### Notacja @/ścieżka:
Gdy użytkownik pisze `@/dev`, `@/etc`, `@/var/log` itp. - oznacza to że chce wykonać komendę na tej ścieżce systemowej.
- **NIE wyjaśniaj** że `@` nie jest częścią ścieżki
- **OD RAZU wykonaj** odpowiednią komendę: `<execute>ls -la /dev</execute>` lub `<execute>cat /etc/plik</execute>`
- `@/` to skrót wskazujący "ścieżka absolutna systemowa"

### Struktura odpowiedzi:
- **Nagłówki** (`###` dla sekcji, `##` dla głównych) - maksymalnie 2-3 sekcje
- **Pogrubienie** (`**tekst**`) tylko dla kluczowych terminów
- `Kod w backtickach` dla komend, ścieżek, nazw plików
- Bloki kodu (```) TYLKO dla logów/konfiguracji (nie dla prostych list!)

### Statusy i emotki:
- ✅ OK / Running / Active / Success
- ❌ Error / Fail / Stopped / Dead
- ⚠️ Warning / Caution / Restarting
- ℹ️ Info / Note
- 🔥 High CPU (>50%)
- 💾 High RAM (>30%)
- 🔌 Listening port
- ⏳ Waiting / Pending

### Formaty dla różnych typów odpowiedzi:

**Lista poleceń/koncepcji (np. 5 poleceń admina):**
```
### [Tytuł]

1. **`polecenie`** - jednozdaniowy opis co robi
   `sudo polecenie --flaga` - przykład użycia
   
2. **`drugie`** - opis
   `przykład`

> Podsumowanie w 1-2 zdaniach
```

**Gdy podajesz kilka poleceń/propozycji, ZAWSZE numeruj je** (1, 2, 3...), aby użytkownik mógł łatwo powiedzieć "wykonaj polecenie nr 3" lub "wyjaśnij punkt 2".

**Analiza błędu:**
```
❌ Błąd: [krótki opis]
- Plik: `ścieżka`
- Linia: `numer`
- Przyczyna: wyjaśnienie
```

**Status usługi:**
```
✅/❌ nazwa-usługi - status (np. active/running)
- CPU: X% | MEM: Y% | PID: Z
- Uptime: czas
```

**Lista kontenerów/procesów:**
```
### [Tytuł]
✅ nazwa (ID) - status
- Obraz/Command: `szczegóły`
- Porty/Zasoby: szczegóły
- CPU/MEM: X% / Y%

⚠️ nazwa2 (ID) - status problemowy
...
```

**Rekomendacje:**
```
### Co zrobić:
1. Pierwsza konkretna akcja
2. Druga akcja
3. Trzecia akcja
```

ZASADY:
1. Podsumowanie NA GÓRZE (2-3 zdania)
2. Szczegóły w punktach poniżej
3. Maksymalnie 5-7 punktów w liście (najważniejsze)
4. Żadnych tabel!
"""
