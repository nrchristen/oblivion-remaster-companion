# Placeholder for data loader tests
import unittest
import os
import sys
import json
from unittest.mock import patch, mock_open, MagicMock

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

# --- New Tests for Save Functionality --- 
class TestSaveData(unittest.TestCase):

    def setUp(self):
        # Ensure DATA_DIR is set for tests, patching might be needed if it relies on __file__ complexly
        # For simplicity, let's assume data_loader.DATA_DIR is correctly defined or mock it.
        self.test_data_dir = '/fake/data'
        data_loader.DATA_DIR = self.test_data_dir # Override for testing

    @patch('builtins.open', new_callable=mock_open)
    @patch('src.data_loader.os.path.join')
    def test_save_json_data_success(self, mock_join, mock_file):
        filename = "test_save.json"
        test_data = {"a": 1, "b": [2, 3]}
        # Construct expected path manually to avoid calling the mocked os.path.join here
        # Use os.sep for platform independence
        expected_path = self.test_data_dir + os.sep + filename
        # Or more robustly: expected_path = os.path.normpath(f"{self.test_data_dir}/{filename}")
        
        # Set the return value for the *actual* call inside save_json_data
        mock_join.return_value = expected_path

        result = data_loader.save_json_data(filename, test_data)

        self.assertTrue(result)
        # Now assert_called_once_with should pass as only the function under test called it
        mock_join.assert_called_once_with(self.test_data_dir, filename)
        mock_file.assert_called_once_with(expected_path, 'w', encoding='utf-8')
        
        # Verify the *content* written matches the expected formatted JSON
        handle = mock_file()
        # Get all arguments passed to write calls
        written_content = "".join(call_args[0][0] for call_args in handle.write.call_args_list)
        expected_content = json.dumps(test_data, indent=2)
        self.assertEqual(written_content, expected_content)

    @patch('builtins.open', side_effect=IOError("Disk full"))
    @patch('src.data_loader.os.path.join')
    @patch('builtins.print') # Suppress error print during test
    def test_save_json_data_io_error(self, mock_print, mock_join, mock_file):
        mock_join.return_value = '/fake/data/fail.json'
        result = data_loader.save_json_data("fail.json", {"a": 1})
        self.assertFalse(result)

    @patch('src.data_loader.load_json_data')
    @patch('src.data_loader.save_json_data')
    def test_add_battle_preset_success_new_file(self, mock_save, mock_load):
        preset_name = "My Battle"
        commands = ["cmd1", "cmd2"]
        mock_load.return_value = None # Simulate file not existing or load error
        mock_save.return_value = True

        status = data_loader.add_battle_preset(preset_name, commands)

        self.assertEqual(status, "success")
        mock_load.assert_called_once_with("battles.json")
        mock_save.assert_called_once_with("battles.json", {preset_name: commands})

    @patch('src.data_loader.load_json_data')
    @patch('src.data_loader.save_json_data')
    def test_add_battle_preset_success_existing_file(self, mock_save, mock_load):
        preset_name = "New Battle"
        commands = ["cmd3"]
        existing_presets = {"Old Battle": ["cmd0"]}
        mock_load.return_value = existing_presets
        mock_save.return_value = True

        status = data_loader.add_battle_preset(preset_name, commands)

        self.assertEqual(status, "success")
        expected_saved_data = {"Old Battle": ["cmd0"], preset_name: commands}
        mock_save.assert_called_once_with("battles.json", expected_saved_data)

    @patch('src.data_loader.load_json_data')
    @patch('src.data_loader.save_json_data')
    def test_add_battle_preset_name_exists(self, mock_save, mock_load):
        preset_name = "Existing Battle"
        commands = ["cmd1"]
        mock_load.return_value = {preset_name: ["old_cmd"]}

        status = data_loader.add_battle_preset(preset_name, commands)

        self.assertEqual(status, "exists")
        mock_save.assert_not_called()

    @patch('src.data_loader.load_json_data')
    @patch('src.data_loader.save_json_data')
    @patch('builtins.print') # Suppress error print
    def test_add_battle_preset_save_error(self, mock_print, mock_save, mock_load):
        mock_load.return_value = {}
        mock_save.return_value = False # Simulate save failure

        status = data_loader.add_battle_preset("Test", ["cmd"])

        self.assertEqual(status, "error")
        mock_save.assert_called_once()

    @patch('builtins.print') # Suppress error print
    def test_add_battle_preset_invalid_input(self, mock_print):
        status_no_name = data_loader.add_battle_preset("", ["cmd"])
        status_no_cmd = data_loader.add_battle_preset("Name", None)
        self.assertEqual(status_no_name, "error")
        self.assertEqual(status_no_cmd, "error")

if __name__ == '__main__':
    unittest.main() 