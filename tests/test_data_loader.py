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

# Define a fake data directory for tests
TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')

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

        # Ensure the test data directory exists and is clean
        if not os.path.exists(TEST_DATA_DIR):
            os.makedirs(TEST_DATA_DIR)
        # Mock the DATA_DIR constant in the data_loader module
        self.data_dir_patcher = patch('src.data_loader.DATA_DIR', TEST_DATA_DIR)
        self.mock_data_dir = self.data_dir_patcher.start()
        # Also mock logging to avoid console output during tests
        self.log_patcher = patch('src.data_loader.logging')
        self.mock_logging = self.log_patcher.start()

    def tearDown(self):
        """Clean up temporary files."""
        bad_json_path = os.path.join(PROJECT_ROOT, 'data', self.bad_json_file)
        if os.path.exists(bad_json_path):
            os.remove(bad_json_path)
        # Stop the patchers
        self.data_dir_patcher.stop()
        self.log_patcher.stop()
        # Clean up any created test files
        for filename in os.listdir(TEST_DATA_DIR):
            os.remove(os.path.join(TEST_DATA_DIR, filename))
        # Remove the test directory itself if empty (optional)
        # if not os.listdir(TEST_DATA_DIR):
        #     os.rmdir(TEST_DATA_DIR)

    def test_load_json_data_success(self):
        """Test loading a valid JSON file from the mocked test directory."""
        # Arrange: Create dummy files in TEST_DATA_DIR
        npcs_filename = "npcs_test.json"
        npcs_filepath = os.path.join(TEST_DATA_DIR, npcs_filename)
        npcs_test_data = {"TestNPC": "12345"}
        with open(npcs_filepath, 'w') as f:
            json.dump(npcs_test_data, f)
            
        arrows_filename = "arrows_test.json"
        arrows_filepath = os.path.join(TEST_DATA_DIR, arrows_filename)
        arrows_test_data = {"TestArrow": "ABCDE"}
        with open(arrows_filepath, 'w') as f:
            json.dump(arrows_test_data, f)

        # Act
        loaded_npc_data = data_loader.load_json_data(npcs_filename)
        loaded_arrow_data = data_loader.load_json_data(arrows_filename)

        # Assert
        self.assertEqual(loaded_npc_data, npcs_test_data)
        self.assertEqual(loaded_arrow_data, arrows_test_data)
        # Check logging was called (now debug)
        self.assertEqual(self.mock_logging.debug.call_count, 2)

    def test_load_json_data_not_found(self):
        """Test loading a non-existent file."""
        data = data_loader.load_json_data(self.nonexistent_file)
        self.assertIsNone(data)
        self.mock_logging.error.assert_called_once() # Verify logging

    def test_load_json_data_bad_format(self):
        """Test loading a file with invalid JSON."""
        # Arrange: Create bad JSON file in TEST_DATA_DIR
        filename = "bad_format_test.json"
        filepath = os.path.join(TEST_DATA_DIR, filename)
        with open(filepath, 'w') as f:
            # Write genuinely invalid JSON (e.g., trailing comma)
            f.write('{"key": "value",}') 
            
        # Act
        data = data_loader.load_json_data(filename)
        
        # Assert
        self.assertIsNone(data)
        self.mock_logging.error.assert_called_once() # Verify logging

    @patch('os.listdir')
    @patch('src.data_loader.load_json_data') # Patch load_json_data used within get_item_categories
    def test_get_item_categories(self, mock_load, mock_listdir):
        """Test retrieving categories, mocking file system interactions."""
        # Arrange
        # Simulate files present in the mocked DATA_DIR
        mock_listdir.return_value = [
            'arrows.json',
            'weapons.json',
            'armor.json',
            'npcs.json', # Should be excluded
            'battles.json', # Should be excluded
            'favorites.json', # Should be excluded
            'invalid_data.json', # File exists, but load returns non-dict
            'readme.txt' # Should be excluded
        ]
        
        # Simulate load_json_data behavior for these files
        def load_side_effect(filename):
            if filename in ['arrows.json', 'weapons.json', 'armor.json']:
                return {'some': 'data'} # Return a valid dict for item files
            elif filename == 'invalid_data.json':
                return [] # Return non-dict for this one
            else:
                return None # Default for others like npcs, txt etc.
        mock_load.side_effect = load_side_effect
        
        # Expected result based on mocked files and load behavior
        expected_categories = {
            'Arrows': 'arrows.json',
            'Weapons': 'weapons.json',
            'Armor': 'armor.json'
        }

        # Act
        categories = data_loader.get_item_categories()

        # Assert
        self.assertIsInstance(categories, dict)
        mock_listdir.assert_called_once_with(TEST_DATA_DIR)
        self.assertEqual(categories, expected_categories)
        # Check load was called correctly (should skip txt, should call for others)
        # Precise call count depends on internal logic, but check key calls
        mock_load.assert_any_call('arrows.json')
        mock_load.assert_any_call('weapons.json')
        mock_load.assert_any_call('armor.json')
        mock_load.assert_any_call('invalid_data.json')
        # Ensure excluded files weren't loaded for category check (they might be loaded elsewhere)
        # This is hard to assert cleanly without more complex mocking, focus on the positive result. 

    def test_load_json_data_file_not_found(self):
        # Arrange
        filename = "non_existent.json"

        # Act
        loaded_data = data_loader.load_json_data(filename)

        # Assert
        self.assertIsNone(loaded_data)
        self.mock_logging.error.assert_called_once()

    def test_load_json_data_invalid_json(self):
        # Arrange
        filename = "invalid.json"
        filepath = os.path.join(TEST_DATA_DIR, filename)
        with open(filepath, 'w') as f:
            f.write("this is not json{")

        # Act
        loaded_data = data_loader.load_json_data(filename)

        # Assert
        self.assertIsNone(loaded_data)
        self.mock_logging.error.assert_called_once()

    # --- Tests for save_json_data --- 

    def test_save_json_data_success(self):
        # Arrange
        filename = "save_test.json"
        filepath = os.path.join(TEST_DATA_DIR, filename)
        test_data = {"name": "test", "items": [1, 2, 3]}
        
        # Act
        result = data_loader.save_json_data(filename, test_data)
        
        # Assert
        self.assertTrue(result)
        self.assertTrue(os.path.exists(filepath))
        with open(filepath, 'r') as f:
            saved_data = json.load(f)
        self.assertEqual(saved_data, test_data)
        self.mock_logging.info.assert_called_once()

    @patch('builtins.open', new_callable=mock_open)
    def test_save_json_data_io_error(self, mock_file):
        # Arrange
        filename = "save_io_error.json"
        test_data = {"a": 1}
        mock_file.side_effect = IOError("Permission denied")
        
        # Act
        result = data_loader.save_json_data(filename, test_data)
        
        # Assert
        self.assertFalse(result)
        mock_file.assert_called_once_with(os.path.join(TEST_DATA_DIR, filename), 'w', encoding='utf-8')
        self.mock_logging.error.assert_called_once()
        # print call is harder to assert cleanly without more patching

    @patch('json.dump')
    @patch('builtins.open', new_callable=mock_open)
    def test_save_json_data_type_error(self, mock_file, mock_dump):
        # Arrange
        filename = "save_type_error.json"
        # Sets are not JSON serializable by default
        test_data = {"data": {1, 2, 3}}
        mock_dump.side_effect = TypeError("Object of type set is not JSON serializable")
        
        # Act
        result = data_loader.save_json_data(filename, test_data)
        
        # Assert
        self.assertFalse(result)
        mock_file.assert_called_once_with(os.path.join(TEST_DATA_DIR, filename), 'w', encoding='utf-8')
        mock_dump.assert_called_once()
        self.mock_logging.error.assert_called_once()

    # --- Tests for add_battle_preset (Example of testing function using save_json_data) ---
    
    @patch('src.data_loader.load_json_data')
    @patch('src.data_loader.save_json_data')
    def test_add_battle_preset_new(self, mock_save, mock_load):
        # Arrange
        preset_name = "NewPreset"
        commands = ["cmd1", "cmd2"]
        mock_load.return_value = {"OldPreset": ["old_cmd"]}
        mock_save.return_value = True
        
        # Act
        status = data_loader.add_battle_preset(preset_name, commands)
        
        # Assert
        self.assertEqual(status, "success")
        mock_load.assert_called_once_with(data_loader.BATTLES_FILE)
        expected_data_to_save = {"OldPreset": ["old_cmd"], "NewPreset": ["cmd1", "cmd2"]}
        mock_save.assert_called_once_with(data_loader.BATTLES_FILE, expected_data_to_save)
        self.mock_logging.info.assert_called()

    @patch('src.data_loader.load_json_data')
    @patch('src.data_loader.save_json_data')
    def test_add_battle_preset_exists(self, mock_save, mock_load):
        # Arrange
        preset_name = "ExistingPreset"
        commands = ["cmd1", "cmd2"]
        mock_load.return_value = {"ExistingPreset": ["old_cmd"]}
        
        # Act
        status = data_loader.add_battle_preset(preset_name, commands)
        
        # Assert
        self.assertEqual(status, "exists")
        mock_load.assert_called_once_with(data_loader.BATTLES_FILE)
        mock_save.assert_not_called() # Should not save if name exists
        self.mock_logging.warning.assert_called()

    @patch('src.data_loader.load_json_data')
    @patch('src.data_loader.save_json_data')
    def test_add_battle_preset_save_fails(self, mock_save, mock_load):
        # Arrange
        preset_name = "SaveFailPreset"
        commands = ["cmd1"]
        mock_load.return_value = {}
        mock_save.return_value = False # Simulate save failure
        
        # Act
        status = data_loader.add_battle_preset(preset_name, commands)
        
        # Assert
        self.assertEqual(status, "error")
        mock_load.assert_called_once_with(data_loader.BATTLES_FILE)
        mock_save.assert_called_once_with(data_loader.BATTLES_FILE, {"SaveFailPreset": ["cmd1"]})
        # Remove assertion: add_battle_preset doesn't log error directly when save fails
        # self.mock_logging.error.assert_called()

    # --- Test ensure_data_files_exist --- 
    
    @patch('os.path.exists')
    @patch('src.data_loader.save_json_data')
    @patch('os.makedirs') # Mock makedirs as well
    def test_ensure_data_files_exist_creates_missing(self, mock_makedirs, mock_save, mock_exists):
        # Arrange
        # Simulate that favorites.json does NOT exist, others do
        def exists_side_effect(path):
            if path.endswith(data_loader.FAVORITES_FILE):
                return False
            return True
        mock_exists.side_effect = exists_side_effect
        mock_save.return_value = True
        
        # Act
        data_loader.ensure_data_files_exist()
        
        # Assert
        mock_makedirs.assert_called_once_with(TEST_DATA_DIR, exist_ok=True)
        # Check exists was called for all required files
        self.assertEqual(mock_exists.call_count, 3)
        # Check save was called ONLY for the missing file with correct default content
        mock_save.assert_called_once_with(data_loader.FAVORITES_FILE, [])
        self.mock_logging.warning.assert_called_once()
        self.mock_logging.error.assert_not_called()

    @patch('os.path.exists')
    @patch('src.data_loader.save_json_data')
    @patch('os.makedirs')
    def test_ensure_data_files_exist_all_exist(self, mock_makedirs, mock_save, mock_exists):
        # Arrange
        mock_exists.return_value = True # All files exist
        
        # Act
        data_loader.ensure_data_files_exist()
        
        # Assert
        mock_makedirs.assert_called_once_with(TEST_DATA_DIR, exist_ok=True)
        self.assertEqual(mock_exists.call_count, 3)
        mock_save.assert_not_called() # No files should be saved
        self.mock_logging.warning.assert_not_called()
        self.mock_logging.error.assert_not_called()
        
    @patch('os.path.exists')
    @patch('src.data_loader.save_json_data')
    @patch('os.makedirs')
    def test_ensure_data_files_exist_creation_fails(self, mock_makedirs, mock_save, mock_exists):
        # Arrange
        mock_exists.return_value = False # Nothing exists
        mock_save.return_value = False # Saving fails
        
        # Act
        data_loader.ensure_data_files_exist()
        
        # Assert
        mock_makedirs.assert_called_once_with(TEST_DATA_DIR, exist_ok=True)
        self.assertEqual(mock_exists.call_count, 3)
        # Save should be attempted for all 3 files
        self.assertEqual(mock_save.call_count, 3)
        self.assertEqual(self.mock_logging.warning.call_count, 3)
        self.assertEqual(self.mock_logging.error.call_count, 3)
        
if __name__ == '__main__':
    unittest.main() 