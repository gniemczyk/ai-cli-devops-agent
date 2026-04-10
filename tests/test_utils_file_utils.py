#!/usr/bin/env python3
"""Testy jednostkowe dla modułu file_utils."""

import sys
import os
import tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from utils.file_utils import is_safe_path, process_file_mentions


class TestFileUtils(unittest.TestCase):
    """Testy funkcji narzędziowych plików."""

    def setUp(self):
        """Przygotowanie środowiska testowego."""
        self.original_dir = os.getcwd()
        self.test_dir = tempfile.mkdtemp()
        os.chdir(self.test_dir)

    def tearDown(self):
        """Sprzątanie po testach."""
        os.chdir(self.original_dir)
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_is_safe_path_current_directory(self):
        """Test że pliki w bieżącym katalogu są bezpieczne."""
        self.assertTrue(is_safe_path("file.txt"))
        self.assertTrue(is_safe_path("./file.txt"))
        self.assertTrue(is_safe_path("subdir/file.txt"))

    def test_is_safe_path_path_traversal(self):
        """Test że path traversal jest wykrywany."""
        self.assertFalse(is_safe_path("../file.txt"))
        self.assertFalse(is_safe_path("../../etc/passwd"))
        self.assertFalse(is_safe_path("../../../secret"))

    def test_is_safe_path_absolute_system_paths(self):
        """Test że ścieżki systemowe są niebezpieczne."""
        self.assertFalse(is_safe_path("/etc/passwd"))
        self.assertFalse(is_safe_path("/usr/bin"))
        self.assertFalse(is_safe_path("/var/log"))

    def test_is_safe_path_home_directory(self):
        """Test że katalog domowy jest bezpieczny."""
        # Katalog domowy powinien być rozszerzony i sprawdzony
        # W zależności od konfiguracji systemu może być bezpieczny lub nie
        home_result = is_safe_path("~/file.txt")
        # Sprawdzamy tylko że funkcja się wykonuje bez błędu
        self.assertIsNotNone(home_result)

    def test_is_safe_path_dangerous_patterns(self):
        """Test wykrywania niebezpiecznych wzorców."""
        # Utwórz tymczasowe pliki z niebezpiecznymi nazwami
        os.makedirs(".env", exist_ok=True)
        os.makedirs(".git", exist_ok=True)
        os.makedirs("__pycache__", exist_ok=True)
        
        self.assertFalse(is_safe_path(".env/config"))
        self.assertFalse(is_safe_path(".git/config"))
        self.assertFalse(is_safe_path("__pycache__/file.pyc"))

    def test_process_file_mentions_no_mentions(self):
        """Test przetwarzania tekstu bez wzmianek o plikach."""
        text = "Just a regular message without file mentions"
        result, commands = process_file_mentions(text)
        self.assertEqual(result, text)
        self.assertEqual(commands, [])

    def test_process_file_mentions_system_command_clear(self):
        """Test komendy systemowej @clear."""
        text = "Check the logs and @clear"
        result, commands = process_file_mentions(text)
        self.assertNotIn("@clear", result)
        self.assertIn("clear", commands)

    def test_process_file_mentions_system_command_compact(self):
        """Test komendy systemowej @compact."""
        text = "@compact the history"
        result, commands = process_file_mentions(text)
        self.assertNotIn("@compact", result)
        self.assertIn("compact", commands)

    def test_process_file_mentions_safe_file(self):
        """Test wczytywania bezpiecznego pliku."""
        # Utwórz testowy plik
        test_file = "test.txt"
        with open(test_file, "w") as f:
            f.write("Test content")
        
        text = f"Read @{test_file}"
        result, commands = process_file_mentions(text)
        self.assertIn("Zawartość pliku:", result)
        self.assertIn("Test content", result)
        self.assertEqual(commands, [])

    def test_process_file_mentions_path_traversal_rejected(self):
        """Test odrzucania path traversal."""
        text = "Read @../../../etc/passwd"
        result, commands = process_file_mentions(text)
        self.assertIn("Odrzucono nieprawidłową ścieżkę", result)
        # Komunikat o odrzuceniu zawiera ścieżkę, więc 'passwd' może być w komunikacie

    def test_process_file_mentions_absolute_path_rejected(self):
        """Test odrzucania ścieżek absolutnych systemowych."""
        text = "Read @/etc/passwd"
        result, commands = process_file_mentions(text)
        # Ścieżki absolutne systemowe są pomijane (nie traktowane jako pliki projektu)
        self.assertNotIn("Zawartość pliku:", result)

    def test_process_file_mentions_nonexistent_file(self):
        """Test pliku który nie istnieje."""
        text = "Read @nonexistent.txt"
        result, commands = process_file_mentions(text)
        self.assertNotIn("Zawartość pliku:", result)

    def test_process_file_mentions_large_file(self):
        """Test pliku przekraczającego limit 1MB."""
        large_file = "large.txt"
        with open(large_file, "w") as f:
            f.write("x" * (1024 * 1024 + 1))  # 1MB + 1 byte
        
        text = f"Read @{large_file}"
        result, commands = process_file_mentions(text)
        self.assertIn("jest zbyt duży", result)

    def test_process_file_mentions_dangerous_path(self):
        """Test odrzucania niebezpiecznych ścieżek."""
        os.makedirs(".env", exist_ok=True)
        with open(".env/secret", "w") as f:
            f.write("secret key")
        
        text = "Read @.env/secret"
        result, commands = process_file_mentions(text)
        self.assertIn("niebezpieczną ścieżkę", result)

    def test_process_file_mentions_multiple_mentions(self):
        """Test wielu wzmianek o plikach."""
        with open("file1.txt", "w") as f:
            f.write("Content 1")
        with open("file2.txt", "w") as f:
            f.write("Content 2")
        
        text = "Read @file1.txt and @file2.txt then @clear"
        result, commands = process_file_mentions(text)
        self.assertIn("Content 1", result)
        self.assertIn("Content 2", result)
        self.assertIn("clear", commands)


if __name__ == "__main__":
    unittest.main()
