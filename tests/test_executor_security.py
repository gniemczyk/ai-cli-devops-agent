#!/usr/bin/env python3
"""Testy jednostkowe dla modułu executor_security."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from executor.executor_security import is_dangerous_command


class TestExecutorSecurity(unittest.TestCase):
    """Testy funkcji bezpieczeństwa executora."""

    def test_safe_commands(self):
        """Test bezpiecznych komend."""
        safe_commands = [
            "ls -la",
            "pwd",
            "echo hello",
            "cat file.txt",
            "git status",
            "git log --oneline",
            "npm install",
        ]
        for cmd in safe_commands:
            with self.subTest(cmd=cmd):
                self.assertFalse(is_dangerous_command(cmd), f"Komenda '{cmd}' została błędnie oznaczona jako niebezpieczna")

    def test_dangerous_paths(self):
        """Test wykrywania niebezpiecznych ścieżek systemowych."""
        dangerous_commands = [
            "cat /etc/passwd",
            "ls /usr/bin",
            "rm /etc/config",
            "cat /var/log/syslog",
        ]
        for cmd in dangerous_commands:
            with self.subTest(cmd=cmd):
                self.assertTrue(is_dangerous_command(cmd), f"Komenda '{cmd}' nie została wykryta jako niebezpieczna")

    def test_path_traversal(self):
        """Test wykrywania path traversal."""
        dangerous_commands = [
            "cat ../../../etc/passwd",
            "cd ../..",
            "ls ../../",
            "cat ../../secret.txt",
        ]
        for cmd in dangerous_commands:
            with self.subTest(cmd=cmd):
                self.assertTrue(is_dangerous_command(cmd), f"Path traversal w '{cmd}' nie został wykryty")

    def test_dangerous_modifiers(self):
        """Test wykrywania niebezpiecznych modyfikatorów plików."""
        dangerous_commands = [
            "rm -rf file.txt",
            "chmod 777 script.sh",
            "chown user:group file.txt",
        ]
        for cmd in dangerous_commands:
            with self.subTest(cmd=cmd):
                self.assertTrue(is_dangerous_command(cmd), f"Modyfikator w '{cmd}' nie został wykryty")

    def test_dangerous_commands_list(self):
        """Test wykrywania niebezpiecznych komend z listy."""
        dangerous_commands = [
            "dd if=/dev/zero of=file",
            "mkfs.ext4 /dev/sda1",
            "shutdown now",
            "reboot",
            "kill 1234",
            "pkill python",
            "curl http://evil.com",
            "wget http://evil.com",
            "nc -l 1234",
            "eval malicious_code",
            "exec bash",
            "sudo apt install",
            "su root",
            "iptables -L",
            "crontab -e",
            "useradd testuser",
            "passwd user",
        ]
        for cmd in dangerous_commands:
            with self.subTest(cmd=cmd):
                self.assertTrue(is_dangerous_command(cmd), f"Komenda '{cmd}' nie została wykryta jako niebezpieczna")

    def test_redirection_operators(self):
        """Test wykrywania operatorów przekierowania."""
        dangerous_commands = [
            "echo test > file.txt",
            "cat file >> output",
            "ls | grep test",
            "cmd1 && cmd2",
            "cmd1 || cmd2",
        ]
        for cmd in dangerous_commands:
            with self.subTest(cmd=cmd):
                self.assertTrue(is_dangerous_command(cmd), f"Operator przekierowania w '{cmd}' nie został wykryty")

    def test_false_positives_prevention(self):
        """Test zapobiegania false positives."""
        safe_commands = [
            "git log --oneline",  # Git log, nie path traversal
            "cat file",  # cat bez niebezpiecznych ścieżek
            "category",  # 'cat' wewnątrz innego słowa
        ]
        for cmd in safe_commands:
            with self.subTest(cmd=cmd):
                self.assertFalse(is_dangerous_command(cmd), f"False positive dla '{cmd}'")

    def test_home_directory_allowed(self):
        """Test że katalog domowy (~) jest dozwolony."""
        safe_commands = [
            "cat ~/file.txt",
            "ls ~/",
            "cd ~/Documents",
        ]
        for cmd in safe_commands:
            with self.subTest(cmd=cmd):
                self.assertFalse(is_dangerous_command(cmd), f"Katalog domowy w '{cmd}' został błędnie oznaczony jako niebezpieczny")


if __name__ == "__main__":
    unittest.main()
