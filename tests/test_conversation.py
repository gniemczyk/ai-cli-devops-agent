#!/usr/bin/env python3
"""Testy jednostkowe dla modułu conversation."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from unittest.mock import Mock, MagicMock
from core.conversation import Conversation


class TestConversation(unittest.TestCase):
    """Testy klasy Conversation."""

    def setUp(self):
        """Przygotowanie środowiska testowego."""
        self.mock_client = Mock()
        self.mock_client.estimate_tokens = Mock(return_value=100)
        self.conversation = Conversation(self.mock_client)

    def test_initialization(self):
        """Test inicjalizacji konwersacji."""
        self.assertIsNotNone(self.conversation.messages)
        self.assertEqual(len(self.conversation.messages), 1)  # Tylko system message
        self.assertEqual(self.conversation.messages[0]["role"], "system")

    def test_add_user_message(self):
        """Test dodawania wiadomości użytkownika."""
        initial_count = len(self.conversation.messages)
        self.conversation.add_user_message("Test message")
        self.assertEqual(len(self.conversation.messages), initial_count + 1)
        self.assertEqual(self.conversation.messages[-1]["role"], "user")
        self.assertEqual(self.conversation.messages[-1]["content"], "Test message")

    def test_add_assistant_message(self):
        """Test dodawania wiadomości asystenta."""
        self.conversation.add_user_message("User message")
        initial_count = len(self.conversation.messages)
        self.conversation.add_assistant_message("Assistant response")
        self.assertEqual(len(self.conversation.messages), initial_count + 1)
        self.assertEqual(self.conversation.messages[-1]["role"], "assistant")
        self.assertEqual(self.conversation.messages[-1]["content"], "Assistant response")

    def test_clear(self):
        """Test czyszczenia historii."""
        self.conversation.add_user_message("Message 1")
        self.conversation.add_assistant_message("Response 1")
        self.conversation.add_user_message("Message 2")
        
        self.assertGreater(len(self.conversation.messages), 1)
        
        self.conversation.clear()
        
        self.assertEqual(len(self.conversation.messages), 1)  # Tylko system message
        self.assertEqual(self.conversation.messages[0]["role"], "system")

    def test_get_messages(self):
        """Test pobierania kopii wiadomości."""
        self.conversation.add_user_message("Test")
        messages = self.conversation.get_messages()
        
        self.assertIsNotNone(messages)
        self.assertEqual(len(messages), len(self.conversation.messages))
        
        # Sprawdź czy to kopia, a nie referencja
        messages.append({"role": "user", "content": "Modified"})
        self.assertNotEqual(len(messages), len(self.conversation.messages))

    def test_remove_last_message(self):
        """Test usuwania ostatniej wiadomości."""
        self.conversation.add_user_message("Message 1")
        self.conversation.add_assistant_message("Response 1")
        initial_count = len(self.conversation.messages)
        
        self.conversation.remove_last_message()
        
        self.assertEqual(len(self.conversation.messages), initial_count - 1)
        self.assertEqual(self.conversation.messages[-1]["role"], "user")

    def test_remove_last_message_empty(self):
        """Test usuwania ostatniej wiadomości gdy została tylko system message."""
        self.conversation.messages = [self.conversation.system_message]
        initial_count = len(self.conversation.messages)
        
        self.conversation.remove_last_message()
        
        # System message nie powinien zostać usunięty (ochrona przed pustą historią)
        self.assertEqual(len(self.conversation.messages), initial_count)

    def test_compress_negative_threshold(self):
        """Test kompresji z ujemnym progiem."""
        with self.assertRaises(ValueError):
            self.conversation.compress(threshold=-1)

    def test_get_token_count(self):
        """Test pobierania liczby tokenów."""
        self.mock_client.estimate_tokens = Mock(return_value=50)
        
        self.conversation.add_user_message("Test message")
        token_count = self.conversation.get_token_count()
        
        self.assertGreater(token_count, 0)


if __name__ == "__main__":
    unittest.main()
