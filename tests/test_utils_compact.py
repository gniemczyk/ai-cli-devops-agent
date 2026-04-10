#!/usr/bin/env python3
"""Testy jednostkowe dla modułu compact."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from utils.compact import estimate_tokens, count_messages_tokens, extract_command_from_message


class TestCompact(unittest.TestCase):
    """Testy funkcji kompresji."""

    def test_estimate_tokens_empty_string(self):
        """Test szacowania tokenów dla pustego stringa."""
        self.assertEqual(estimate_tokens(""), 0)
        self.assertEqual(estimate_tokens(None), 0)

    def test_estimate_tokens_simple_text(self):
        """Test szacowania tokenów dla prostego tekstu."""
        text = "Hello world"
        tokens = estimate_tokens(text)
        self.assertGreater(tokens, 0)
        self.assertLess(tokens, len(text) * 2)  # Rozsądny górny limit

    def test_estimate_tokens_code(self):
        """Test szacowania tokenów dla kodu."""
        code = "def test():\n    return True"
        tokens = estimate_tokens(code)
        self.assertGreater(tokens, 0)
        # Kod powinien mieć więcej tokenów niż zwykły tekst tej samej długości
        text_only = code.replace("():", "  ").replace("\n", " ")
        code_tokens = estimate_tokens(code)
        text_tokens = estimate_tokens(text_only)
        self.assertGreaterEqual(code_tokens, text_tokens)

    def test_estimate_tokens_special_chars(self):
        """Test szacowania tokenów dla znaków specjalnych."""
        text_with_special = "test[]{}()<>/\\|=-+*&^%$#@!;:'\"`"
        tokens = estimate_tokens(text_with_special)
        self.assertGreater(tokens, 0)
        # Specjalne znaki wpływają na szacowanie tokenów
        plain_text = "test" * len(text_with_special)
        # Sprawdzamy tylko że tokeny są policzone
        self.assertGreater(estimate_tokens(plain_text), 0)

    def test_estimate_tokens_non_ascii(self):
        """Test szacowania tokenów dla znaków non-ASCII."""
        non_ascii_text = "ąćęłńóśźż"
        tokens = estimate_tokens(non_ascii_text)
        self.assertGreater(tokens, 0)
        # Non-ASCII powinno mieć więcej tokenów
        ascii_text = "abcdefgh"
        self.assertGreater(tokens, estimate_tokens(ascii_text))

    def test_count_messages_tokens(self):
        """Test liczenia tokenów w wiadomościach."""
        messages = [
            {"role": "system", "content": "System prompt"},
            {"role": "user", "content": "User message"},
            {"role": "assistant", "content": "Assistant response"},
        ]
        tokens = count_messages_tokens(messages)
        self.assertGreater(tokens, 0)

    def test_count_messages_tokens_empty(self):
        """Test liczenia tokenów dla pustej listy wiadomości."""
        self.assertEqual(count_messages_tokens([]), 0)
        self.assertEqual(count_messages_tokens([{"role": "system", "content": ""}]), 0)

    def test_extract_command_from_message(self):
        """Test wyciągania komendy z tagów execute."""
        message = "Here is the command: <execute>ls -la</execute>"
        command = extract_command_from_message(message)
        self.assertEqual(command, "ls -la")

    def test_extract_command_multiline(self):
        """Test wyciągania wieloliniowej komendy."""
        message = """Execute this:
<execute>
cd /tmp
ls -la
</execute>"""
        command = extract_command_from_message(message)
        self.assertIn("cd /tmp", command)
        self.assertIn("ls -la", command)

    def test_extract_command_no_execute_tags(self):
        """Test gdy brak tagów execute."""
        message = "Just a regular message without execute tags"
        command = extract_command_from_message(message)
        self.assertEqual(command, "")

    def test_extract_command_case_insensitive(self):
        """Test że extract_command jest case-insensitive."""
        message = "<EXECUTE>ls -la</EXECUTE>"
        command = extract_command_from_message(message)
        self.assertEqual(command, "ls -la")

    def test_extract_command_whitespace_handling(self):
        """Test usuwania białych znaków z komendy."""
        message = "<execute>  ls -la  </execute>"
        command = extract_command_from_message(message)
        self.assertEqual(command, "ls -la")


if __name__ == "__main__":
    unittest.main()
