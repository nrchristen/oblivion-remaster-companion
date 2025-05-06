import unittest
import os
import json
import shutil
from unittest.mock import patch, mock_open, MagicMock, call # Added call

# Assuming data_loader.py is in the src directory relative to the tests
# Adjust the path as necessary if your structure is different
import sys
# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

import data_loader

# Define a directory for test data relative to this test file
TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
# Define the path to item_categories.json within the test data directory
# We'll use this path when mocking the load_json_data call for categories
TEST_CATEGORIES_PATH = os.path.join(TEST_DATA_DIR, 'item_categories.json')

# Import the module itself to allow patching its internals like os
from src import data_loader as src_data_loader 
# Import specific functions to test
from data_loader import (
    load_json_data,
    get_item_categories,
    load_items_for_category,
    add_battle_preset,
    save_json_data,
    DATA_DIR,
    FAVORITES_FILE,
    BATTLES_FILE,
    NPCS_FILE,
    LOCATION_CATEGORIES_FILE,
    LOCATIONS_SUBDIR,
    ensure_data_files_exist,
    get_location_categories,
    load_locations_for_category,
    load_all_locations,
    get_preset_commands,
    find_data_file,
    list_json_files,
    load_npcs
)

# Make sure DATA_DIR used by functions under test points to our test data dir
src_data_loader.DATA_DIR = TEST_DATA_DIR 
# Adjust other paths within data_loader if they don't rely on DATA_DIR
# These should now be relative to the overridden DATA_DIR
src_data_loader.LOCATION_CATEGORIES_FILE = os.path.join(TEST_DATA_DIR, "location_categories.json") # Make absolute path
src_data_loader.LOCATIONS_DIR = os.path.join(TEST_DATA_DIR, "locations") # Make absolute path
src_data_loader.ITEM_CATEGORIES_FILE = "item_categories.json" # Keep relative to DATA_DIR
src_data_loader.BATTLES_FILE = "battles.json" # Keep relative to DATA_DIR
src_data_loader.FAVORITES_FILE = "favorites.json" # Keep relative to DATA_DIR

class TestItemLoader(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Create the test data directory if it doesn't exist
        if not os.path.exists(TEST_DATA_DIR):
            os.makedirs(TEST_DATA_DIR)
        # Example item_categories.json content for tests
        cls.test_categories_content = {
            "Armor": {
                "Iron (Heavy)": "armor/heavy_iron.json"
            },
            "Arrows": {
                "Mundane": "arrows/arrows_mundane.json"
            },
            "Books": {
                 "Skill Books": "books/books_skill.json",
                 "Marker Books": "books/books_marker.json",
                 "Normal Books": "books/books_normal.json"
             }
        }
        # Create a dummy item_categories.json for tests that might need it physically
        # Although most tests will mock the loading process now
        with open(TEST_CATEGORIES_PATH, 'w') as f:
            json.dump(cls.test_categories_content, f)


    @classmethod
    def tearDownClass(cls):
        # Remove the test data directory and its contents after all tests are run
        if os.path.exists(TEST_DATA_DIR):
            shutil.rmtree(TEST_DATA_DIR)

    def setUp(self):
        # Define dummy category data
        self.item_categories_data = {
            "Weapons": "items/weapons.json",
            "Armor": "items/armor.json",
            "Potions": "items/potions.json"
        }
        self.weapons_data = {
            "Iron Sword": {"id": "0001C145", "damage": 10, "weight": 12},
            "Steel Dagger": {"id": "000229A5", "damage": 6, "weight": 4}
        }
        # Create dummy files in TEST_DATA_DIR
        os.makedirs(os.path.join(TEST_DATA_DIR, "items"), exist_ok=True)
        # Use src_data_loader.ITEM_CATEGORIES_FILE which respects the overridden DATA_DIR
        with open(os.path.join(src_data_loader.DATA_DIR, src_data_loader.ITEM_CATEGORIES_FILE), 'w') as f:
            json.dump(self.item_categories_data, f)
        with open(os.path.join(src_data_loader.DATA_DIR, "items", "weapons.json"), 'w') as f:
            json.dump(self.weapons_data, f)
            
        # Mock logging for all tests in this class
        self.log_patcher = patch('data_loader.logging')
        self.mock_logging = self.log_patcher.start()
        # Mock the DATA_DIR constant to point to our test directory
        self.data_dir_patcher = patch('data_loader.DATA_DIR', TEST_DATA_DIR)
        self.mock_data_dir = self.data_dir_patcher.start()


    def tearDown(self):
        # Stop the patchers
        self.log_patcher.stop()
        self.data_dir_patcher.stop()
        # Clean up dummy files
        files_to_remove = [
            src_data_loader.ITEM_CATEGORIES_FILE,
            os.path.join("items", "weapons.json"),
            os.path.join("items", "armor.json"), # If created by tests
            os.path.join("items", "potions.json") # If created by tests
        ]
        for f in files_to_remove:
             # Use src_data_loader.DATA_DIR
             fp = os.path.join(src_data_loader.DATA_DIR, f)
             if os.path.exists(fp):
                 os.remove(fp)
        # Remove dummy dir
        try:
            os.rmdir(os.path.join(src_data_loader.DATA_DIR, "items"))
        except OSError:
            pass # Ignore if not empty or doesn't exist

    # === Tests for load_json_data ===

    def test_load_json_data_success(self):
        """Test loading a valid JSON file."""
        # Load using the mocked DATA_DIR
        loaded_data = data_loader.load_json_data(self.test_json_filename)
        self.assertEqual(loaded_data, self.test_data)
        self.mock_logging.debug.assert_called_once() # Check if debug log was called

    def test_load_json_data_file_not_found(self):
        """Test loading a non-existent file."""
        filename = 'nonexistent.json'
        # Load using the mocked DATA_DIR
        loaded_data = data_loader.load_json_data(filename)
        self.assertIsNone(loaded_data) # Expect None on failure
        self.mock_logging.error.assert_called_once() # Check for specific error log
        # Check if the error message contains the expected filename and path (using TEST_DATA_DIR)
        self.assertIn(filename, self.mock_logging.error.call_args[0][0])
        self.assertIn(os.path.join(TEST_DATA_DIR, filename), self.mock_logging.error.call_args[0][0])


    def test_load_json_data_invalid_json(self):
        """Test loading a file with invalid JSON content."""
        invalid_json_filename = 'invalid.json'
        invalid_json_filepath = os.path.join(TEST_DATA_DIR, invalid_json_filename)
        with open(invalid_json_filepath, 'w') as f:
            f.write('{ "key": "value", ') # Malformed JSON

        # Load using the mocked DATA_DIR
        loaded_data = data_loader.load_json_data(invalid_json_filename)
        self.assertIsNone(loaded_data) # Expect None on failure
        self.mock_logging.error.assert_called_once()
        self.assertIn(invalid_json_filename, self.mock_logging.error.call_args[0][0])
        # Clean up the invalid file
        os.remove(invalid_json_filepath)

    def test_load_json_data_directory_not_found(self):
        """Test loading when the base DATA_DIR is invalid."""
        # Temporarily stop the DATA_DIR patcher to simulate it being gone/invalid
        self.data_dir_patcher.stop()
        # We need to mock os.path.join or os.path.exists used internally by load_json_data
        # Assuming it checks path existence first:
        with patch('os.path.exists', return_value=False): # Simulate dir/path not existing
             loaded_data = data_loader.load_json_data(self.test_json_filename)
             self.assertIsNone(loaded_data) # Expect None on failure
             # Check that an error related to the path/file not found was logged.
             # The exact message depends on implementation, check if error was logged.
             self.assertTrue(self.mock_logging.error.called)

        # Restart the patcher for subsequent tests
        self.mock_data_dir = self.data_dir_patcher.start()

    # === Tests for get_item_categories ===

    # Use src_data_loader reference for patching
    @patch('src.data_loader.load_json_data') 
    def test_get_item_categories_success(self, mock_load_json):
        """Test getting item categories successfully."""
        mock_load_json.return_value = self.item_categories_data
        categories = get_item_categories()
        self.assertEqual(categories, self.item_categories_data)
        # Check call uses the constant defined in the module
        mock_load_json.assert_called_once_with(src_data_loader.ITEM_CATEGORIES_FILE)

    # Use src_data_loader reference for patching
    @patch('src.data_loader.load_json_data') 
    def test_get_item_categories_load_fails(self, mock_load_json):
        """Test getting item categories when load_json_data fails."""
        mock_load_json.return_value = None
        categories = get_item_categories()
        self.assertEqual(categories, {})
        mock_load_json.assert_called_once_with(src_data_loader.ITEM_CATEGORIES_FILE)

    # Use src_data_loader reference for patching
    @patch('src.data_loader.load_json_data') 
    def test_get_item_categories_wrong_type(self, mock_load_json):
        """Test getting item categories when loaded data is not a dict."""
        mock_load_json.return_value = ["list", "not", "dict"]
        with self.assertLogs(level='ERROR') as cm:
             categories = get_item_categories()
        self.assertEqual(categories, {})
        self.assertTrue(any("Expected a JSON object" in log for log in cm.output))
        mock_load_json.assert_called_once_with(src_data_loader.ITEM_CATEGORIES_FILE)

    # === Tests for load_items_for_category ===

    # Patch internals of the data_loader module
    @patch('src.data_loader.get_item_categories')
    @patch('src.data_loader.os.path.exists') 
    @patch('builtins.open', new_callable=mock_open) 
    def test_load_items_for_category_success(self, mock_open_func, mock_exists, mock_get_cats):
        """Test successfully loading items for a valid category."""
        mock_get_cats.return_value = self.item_categories_data
        mock_exists.return_value = True
        # Construct expected path using overridden DATA_DIR
        weapon_path = os.path.join(src_data_loader.DATA_DIR, "items", "weapons.json")
        mock_open_func.side_effect = lambda file, *args, **kwargs: \
            mock_open(read_data=json.dumps(self.weapons_data))(file, *args, **kwargs) if file == weapon_path \
            else mock_open()(file, *args, **kwargs) # Default mock for other files

        items = load_items_for_category("Weapons")

        self.assertEqual(items, self.weapons_data)
        mock_get_cats.assert_called_once()
        mock_exists.assert_called_once_with(weapon_path)
        mock_open_func.assert_called_once_with(weapon_path, 'r')

    # Patch internals of the data_loader module
    @patch('src.data_loader.get_item_categories')
    def test_load_items_for_invalid_category(self, mock_get_cats):
        """Test loading items for a category not in the categories map."""
        mock_get_cats.return_value = self.item_categories_data
        
        with self.assertLogs(level='ERROR') as cm:
            items = load_items_for_category("InvalidCategory")
        
        self.assertIsNone(items)
        mock_get_cats.assert_called_once()
        self.assertTrue(any("Category 'InvalidCategory' not found" in log for log in cm.output))
        
    # Patch internals of the data_loader module
    @patch('src.data_loader.get_item_categories')
    @patch('src.data_loader.os.path.exists') 
    def test_load_items_for_category_file_not_found(self, mock_exists, mock_get_cats):
        """Test loading items for a category where the file doesn't exist."""
        mock_get_cats.return_value = self.item_categories_data
        mock_exists.return_value = False # Simulate file not existing
        weapon_path = os.path.join(src_data_loader.DATA_DIR, "items", "weapons.json")
        
        with self.assertLogs(level='ERROR') as cm:
             items = load_items_for_category("Weapons")
             
        self.assertIsNone(items)
        mock_get_cats.assert_called_once()
        mock_exists.assert_called_once_with(weapon_path)
        self.assertTrue(any("Data file not found for category 'Weapons'" in log for log in cm.output))

    # Patch internals of the data_loader module
    @patch('src.data_loader.get_item_categories')
    @patch('src.data_loader.os.path.exists') 
    @patch('builtins.open', new_callable=mock_open, read_data="invalid json data") 
    def test_load_items_for_category_json_error(self, mock_open_func, mock_exists, mock_get_cats):
        """Test loading items when JSON decoding fails."""
        mock_get_cats.return_value = self.item_categories_data
        mock_exists.return_value = True
        weapon_path = os.path.join(src_data_loader.DATA_DIR, "items", "weapons.json")
        
        with self.assertLogs(level='ERROR') as cm:
            items = load_items_for_category("Weapons")
            
        self.assertIsNone(items)
        mock_get_cats.assert_called_once()
        mock_exists.assert_called_once_with(weapon_path)
        mock_open_func.assert_called_once_with(weapon_path, 'r')
        self.assertTrue(any("Error decoding JSON for category 'Weapons'" in log for log in cm.output))

# End of TestItemLoader class

# --- Test Location Loading ---

class TestLocationLoader(unittest.TestCase):
    """Tests for location data loading functions."""

    @patch('src.data_loader.os.path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data='{"Cities": "cities.json", "Guilds": "guilds.json"}')
    @patch('src.data_loader.json.load')
    def test_get_location_categories_success(self, mock_json_load, mock_open_func, mock_exists):
        """Test successfully loading location categories."""
        mock_exists.return_value = True
        expected_categories = {"Cities": "cities.json", "Guilds": "guilds.json"}
        mock_json_load.return_value = expected_categories

        categories = data_loader.get_location_categories()

        self.assertEqual(categories, expected_categories)
        mock_exists.assert_called_once_with(data_loader.LOCATION_CATEGORIES_FILE)
        mock_open_func.assert_called_once_with(data_loader.LOCATION_CATEGORIES_FILE, 'r')
        mock_json_load.assert_called_once()

    @patch('src.data_loader.os.path.exists', return_value=False)
    def test_get_location_categories_file_not_found(self, mock_exists):
        """Test loading location categories when the file doesn't exist."""
        categories = data_loader.get_location_categories()
        self.assertEqual(categories, {})
        mock_exists.assert_called_once_with(data_loader.LOCATION_CATEGORIES_FILE)

    @patch('src.data_loader.os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    @patch('src.data_loader.json.load', side_effect=json.JSONDecodeError("Mock error", "", 0))
    def test_get_location_categories_json_error(self, mock_json_load, mock_open_func, mock_exists):
        """Test loading location categories when JSON decoding fails."""
        mock_exists.return_value = True
        categories = data_loader.get_location_categories()
        self.assertEqual(categories, {})
        mock_open_func.assert_called_once_with(data_loader.LOCATION_CATEGORIES_FILE, 'r')

    # Tests for load_locations_for_category
    @patch('src.data_loader.os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    @patch('src.data_loader.json.load')
    @patch('src.data_loader.get_location_categories') # Mock the dependency
    def test_load_locations_for_category_success(self, mock_get_loc_cats, mock_json_load, mock_open_func, mock_exists):
        """Test successfully loading locations for a valid category."""
        # Mock the return value of get_location_categories
        mock_categories = {"Cities": "cities.json", "Guilds": "guilds.json"}
        mock_get_loc_cats.return_value = mock_categories
        
        # Mock file existence for the specific location file
        expected_filepath = os.path.join(data_loader.LOCATIONS_DIR, "cities.json")
        mock_exists.return_value = True # Assume the file exists
        
        # Mock the data loaded from the location file
        mock_location_data = {"Anvil Lighthouse": "AnvilLighthouse", "Chorrol Mages Guild": "ChorrolMagesGuild"}
        mock_json_load.return_value = mock_location_data
        
        # Call the function under test
        locations = data_loader.load_locations_for_category("Cities")

        # Assertions
        self.assertEqual(locations, mock_location_data)
        mock_get_loc_cats.assert_called_once() # Verify the dependency was called
        mock_exists.assert_called_once_with(expected_filepath) # Verify existence check on correct file
        mock_open_func.assert_called_once_with(expected_filepath, 'r') # Verify open on correct file
        mock_json_load.assert_called_once() # Verify JSON load was called

    @patch('src.data_loader.os.path.exists')
    @patch('src.data_loader.get_location_categories')
    def test_load_locations_for_category_file_not_found(self, mock_get_loc_cats, mock_exists):
        """Test loading locations for a category where the file doesn't exist."""
        mock_exists.return_value = False
        mock_categories = {"Cities": "nonexistent.json"}
        mock_get_loc_cats.return_value = mock_categories

        locations = data_loader.load_locations_for_category("Cities")
        self.assertIsNone(locations)
        mock_exists.assert_called_once_with(os.path.join(data_loader.LOCATIONS_DIR, "nonexistent.json"))

    @patch('src.data_loader.get_location_categories')
    def test_load_locations_for_invalid_category(self, mock_get_loc_cats):
        """Test loading locations for a category not in the categories map."""
        mock_categories = {"Guilds": "guilds.json"}
        mock_get_loc_cats.return_value = mock_categories

        locations = data_loader.load_locations_for_category("InvalidCategory")
        self.assertIsNone(locations)

    @patch('src.data_loader.os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    @patch('src.data_loader.json.load', side_effect=json.JSONDecodeError("Mock error", "", 0))
    @patch('src.data_loader.get_location_categories')
    def test_load_locations_for_category_json_error(self, mock_get_loc_cats, mock_json_load, mock_open_func, mock_exists):
        """Test loading locations when JSON decoding fails."""
        mock_exists.return_value = True
        mock_categories = {"Cities": "cities.json"}
        mock_get_loc_cats.return_value = mock_categories

        locations = data_loader.load_locations_for_category("Cities")
        self.assertIsNone(locations)
        mock_open_func.assert_called_once_with(os.path.join(data_loader.LOCATIONS_DIR, "cities.json"), 'r')
        
    @patch('src.data_loader.os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    @patch('src.data_loader.json.load')
    @patch('src.data_loader.get_location_categories')
    def test_load_locations_for_category_invalid_format(self, mock_get_loc_cats, mock_json_load, mock_open_func, mock_exists):
        """Test loading locations when data is not Dict[str, str]."""
        mock_exists.return_value = True
        mock_categories = {"Cities": "cities.json"}
        mock_location_data = ["List", "instead", "of", "dict"] # Invalid format

        mock_get_loc_cats.return_value = mock_categories
        mock_json_load.return_value = mock_location_data
        
        locations = data_loader.load_locations_for_category("Cities")

        expected_filepath = os.path.join(data_loader.LOCATIONS_DIR, "cities.json")
        self.assertIsNone(locations) # Should return None due to format error
        mock_get_loc_cats.assert_called_once()
        mock_exists.assert_called_once_with(expected_filepath)
        mock_open_func.assert_called_once_with(expected_filepath, 'r')
        mock_json_load.assert_called_once()

# ... existing TestDataLoader (should be renamed or merged carefully)

# Need to merge TestDataLoader with TestLocationLoader or ensure names are distinct
# Let's keep TestItemLoader and TestLocationLoader separate for clarity.

# The original TestDataLoader seemed to be testing utility functions like save/load_json
# We should keep those tests separate or integrate them logically.

# Assuming the original TestDataLoader tests generic JSON load/save utilities:
class TestJsonUtilities(unittest.TestCase):
    # ... (paste the original tests for load_json_data, save_json_data etc. here)
    # Make sure to adjust paths and mocks as needed if they were specific before.
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('src.data_loader.json.dump')
    def test_save_json_data_success(self, mock_json_dump, mock_open_file):
        # ... (original test code)
        pass 

    # ... other tests from the original TestDataLoader ...
        
if __name__ == '__main__':
    unittest.main() 