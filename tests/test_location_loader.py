import unittest
import os
import json
from unittest.mock import patch, mock_open

# Assuming the loader function will be in src.data_loader
# Adjust the import path if necessary
from src.data_loader import load_all_locations

class TestLocationLoader(unittest.TestCase):

    def setUp(self):
        # Define dummy data simulating the JSON files
        self.dummy_locations_dir = os.path.abspath('dummy_data/locations') # Use absolute path for consistency
        self.dummy_cities = {'City A': 'CityAID', 'City B': 'CityBID'}
        self.dummy_guilds = {'Guild X': 'GuildXID', 'Guild Y': 'GuildYID'}
        self.dummy_houses = {'House 1': 'House1ID'}

        # Create mock JSON content using normalized paths
        self.mock_files = {
            os.path.normpath(os.path.join(self.dummy_locations_dir, 'cities.json')): json.dumps(self.dummy_cities),
            os.path.normpath(os.path.join(self.dummy_locations_dir, 'guilds.json')): json.dumps(self.dummy_guilds),
            os.path.normpath(os.path.join(self.dummy_locations_dir, 'houses.json')): json.dumps(self.dummy_houses),
            os.path.normpath(os.path.join(self.dummy_locations_dir, 'not_a_location.txt')): 'some text data',
        }

    @patch('src.data_loader.os.path.isdir') # Patch where it's used
    @patch('src.data_loader.os.listdir')    # Patch where it's used
    @patch('builtins.open', new_callable=mock_open) 
    # Removed isfile mock from decorator
    def test_load_all_locations(self, mock_open_func, mock_listdir, mock_isdir):
        # Configure mocks
        mock_isdir.return_value = True # Simulate directory exists
        mock_listdir.return_value = ['cities.json', 'guilds.json', 'houses.json', 'not_a_location.txt']

        # Set up mock_open to return the correct content for each file
        def side_effect(file, *args, **kwargs):
            normalized_file = os.path.normpath(os.path.abspath(file)) # Normalize and make absolute
            # print(f"DEBUG: Mock open called with: {normalized_file}") # Debug print
            # print(f"DEBUG: Known mock files: {list(self.mock_files.keys())}") # Debug print
            if normalized_file in self.mock_files:
                # print(f"DEBUG: Mocking file: {normalized_file}")
                return mock_open(read_data=self.mock_files[normalized_file])(file, *args, **kwargs)
            else:
                # print(f"DEBUG: File not found in mock: {normalized_file}")
                raise FileNotFoundError(f"[Mock] File not found: {normalized_file}")
        mock_open_func.side_effect = side_effect

        # Call the function under test
        # Pass the same dummy dir used in setUp
        locations = load_all_locations(self.dummy_locations_dir) 

        # Assertions
        expected_locations = {}
        expected_locations.update(self.dummy_cities)
        expected_locations.update(self.dummy_guilds)
        expected_locations.update(self.dummy_houses)
        # Sort the expected locations like the function does
        expected_locations = dict(sorted(expected_locations.items()))

        # Check that listdir was called with the correct path
        mock_listdir.assert_called_once_with(self.dummy_locations_dir)

        # Check that open was called for each JSON file (using normalized, absolute paths)
        expected_calls = [
            unittest.mock.call(os.path.normpath(os.path.join(self.dummy_locations_dir, 'cities.json')), 'r', encoding='utf-8'),
            unittest.mock.call(os.path.normpath(os.path.join(self.dummy_locations_dir, 'guilds.json')), 'r', encoding='utf-8'),
            unittest.mock.call(os.path.normpath(os.path.join(self.dummy_locations_dir, 'houses.json')), 'r', encoding='utf-8'),
        ]
        # Check calls were made, order might vary
        mock_open_func.assert_has_calls(expected_calls, any_order=True)
        # Ensure it wasn't called for the non-json file
        self.assertNotIn(
            unittest.mock.call(os.path.normpath(os.path.join(self.dummy_locations_dir, 'not_a_location.txt')), 'r', encoding='utf-8'),
            mock_open_func.call_args_list
        )

        # Check the combined dictionary is correct
        self.assertEqual(locations, expected_locations)

    @patch('src.data_loader.os.path.isdir')
    @patch('src.data_loader.os.listdir')
    def test_load_all_locations_empty_dir(self, mock_listdir, mock_isdir):
        # Configure mocks
        mock_isdir.return_value = True
        mock_listdir.return_value = []

        # Call the function under test
        locations = load_all_locations(self.dummy_locations_dir)

        # Assertions
        mock_listdir.assert_called_once_with(self.dummy_locations_dir)
        self.assertEqual(locations, {}) # Should return an empty dict

    @patch('src.data_loader.os.path.isdir')
    @patch('src.data_loader.os.listdir')
    @patch('builtins.open', new_callable=mock_open, read_data='invalid json')
    # Removed isfile mock from decorator
    def test_load_all_locations_invalid_json(self, mock_open_func, mock_listdir, mock_isdir):
        # Configure mocks
        mock_isdir.return_value = True
        mock_listdir.return_value = ['invalid.json']
        invalid_file_path = os.path.normpath(os.path.join(self.dummy_locations_dir, 'invalid.json'))

        # Need to set the side_effect for mock_open here too if we want it to handle the specific file
        # Otherwise, the read_data='invalid json' applies to any open call
        mock_open_func.side_effect = lambda file, *args, **kwargs: \
            mock_open(read_data='invalid json')(file, *args, **kwargs) if os.path.normpath(os.path.abspath(file)) == invalid_file_path \
            else mock_open()(file, *args, **kwargs)

        # Call the function - it should handle the error gracefully
        with self.assertLogs(level='ERROR') as cm:
            locations = load_all_locations(self.dummy_locations_dir)

        # Assertions
        mock_isdir.assert_called_once_with(self.dummy_locations_dir)
        mock_listdir.assert_called_once_with(self.dummy_locations_dir)
        mock_open_func.assert_called_once_with(invalid_file_path, 'r', encoding='utf-8')
        self.assertEqual(locations, {}) # Should be empty if the only file was invalid
        # Check if an error was logged
        self.assertTrue(any('Error loading JSON' in log for log in cm.output))
        # Removed isfile assertion


if __name__ == '__main__':
    unittest.main() 