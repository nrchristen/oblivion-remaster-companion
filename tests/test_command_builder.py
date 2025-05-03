# Placeholder for command builder tests
import unittest
import os
import sys

# Add src directory to allow importing modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from command_builder import (
    build_simple_command,
    build_placeatme_command,
    build_additem_command
)

class TestCommandBuilder(unittest.TestCase):

    def test_build_simple_command(self):
        self.assertEqual(build_simple_command("ghost"), "ghost")
        self.assertEqual(build_simple_command(" walk "), "walk")
        self.assertIsNone(build_simple_command(""))
        self.assertIsNone(build_simple_command(None))
        self.assertIsNone(build_simple_command(123))

    def test_build_placeatme_command(self):
        self.assertEqual(build_placeatme_command("00024166", 1), "player.placeatme 00024166 1")
        self.assertEqual(build_placeatme_command(" 000ABCDEF ", 5), "player.placeatme 000ABCDEF 5")
        self.assertIsNone(build_placeatme_command("", 1))
        self.assertIsNone(build_placeatme_command(None, 1))
        self.assertIsNone(build_placeatme_command("12345", 0))
        self.assertIsNone(build_placeatme_command("12345", -1))
        self.assertIsNone(build_placeatme_command("12345", None))
        self.assertIsNone(build_placeatme_command(12345, 1))

    def test_build_additem_command(self):
        self.assertEqual(build_additem_command("0800BA54", 1), "player.additem 0800BA54 1")
        self.assertEqual(build_additem_command(" 000FEDCBA ", 10), "player.additem 000FEDCBA 10")
        self.assertIsNone(build_additem_command("", 1))
        self.assertIsNone(build_additem_command(None, 1))
        self.assertIsNone(build_additem_command("54321", 0))
        self.assertIsNone(build_additem_command("54321", -5))
        self.assertIsNone(build_additem_command("54321", None))
        self.assertIsNone(build_additem_command(54321, 1))

if __name__ == '__main__':
    unittest.main() 