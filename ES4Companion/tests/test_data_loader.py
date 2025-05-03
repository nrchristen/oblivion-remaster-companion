# Placeholder for data loader tests
import unittest
import os
import sys
import json

# Add src directory to allow importing modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
# Add project root to access data files relative to it
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

from src import data_loader

class TestDataLoader(unittest.TestCase):

    # Note: These tests rely on the actual JSON files existing in ../data/
    # Consider using mock files for more isolated testing.

    def setUp(self):
        """Set up test data directory for clarity."""
        self.data_dir_relative_to_test = os.path.join('..', 'data')
        self.npcs_file = 'npcs.json'
        self.arrows_file = 'arrows.json'
        self.nonexistent_file = 'nonexistent123.json'
        self.bad_json_file = 'bad_format.json'
        self.item_categories_expected = {
            'Alchemy equipment', 'Alchemy ingredients', 'Armor', 'Arrows',
            'Backpack', 'Horses', 'Locations', 'Weapons'
        }

        # Create a temporary bad JSON file
        bad_json_path = os.path.join(PROJECT_ROOT, 'data', self.bad_json_file)
        with open(bad_json_path, 'w') as f:
            # Use a different invalid JSON format (missing closing brace)
            f.write('{"key": "value"')

    def tearDown(self):
        """Clean up temporary files."""
        bad_json_path = os.path.join(PROJECT_ROOT, 'data', self.bad_json_file)
        if os.path.exists(bad_json_path):
            os.remove(bad_json_path)

    def test_load_json_data_success(self):
        """Test loading a valid JSON file."""
        npc_data = data_loader.load_json_data(self.npcs_file)
        self.assertIsNotNone(npc_data)
        self.assertIsInstance(npc_data, dict)
        self.assertIn("Azzan", npc_data)
        self.assertEqual(npc_data["Azzan"], "00024166")

        arrow_data = data_loader.load_json_data(self.arrows_file)
        self.assertIsNotNone(arrow_data)
        self.assertIsInstance(arrow_data, dict)
        self.assertIn("Arrow of Apathy", arrow_data)
        self.assertEqual(arrow_data["Arrow of Apathy"], "0800BA54")

    def test_load_json_data_not_found(self):
        """Test loading a non-existent file."""
        data = data_loader.load_json_data(self.nonexistent_file)
        self.assertIsNone(data)

    def test_load_json_data_bad_format(self):
        """Test loading a file with invalid JSON."""
        data = data_loader.load_json_data(self.bad_json_file)
        self.assertIsNone(data)

    def test_get_item_categories(self):
        """Test retrieving the list of item categories."""
        categories = data_loader.get_item_categories()
        self.assertIsInstance(categories, dict)
        # Check if the set of retrieved category names matches the expected set
        self.assertEqual(set(categories.keys()), self.item_categories_expected)
        # Check if a specific category maps to the correct filename
        self.assertEqual(categories['Arrows'], self.arrows_file)
        self.assertNotIn('Npcs', categories) # Should exclude npcs.json

if __name__ == '__main__':
    unittest.main() 