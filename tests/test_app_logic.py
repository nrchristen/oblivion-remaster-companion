import unittest
from unittest.mock import patch, MagicMock, ANY, call
import os
import sys
import time # Import time for mocking sleep if needed

# Ensure src is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Module to test
from src import app_logic
# Also need to patch the globals it uses from app
import app
from src import data_loader # Needed for constants like FAVORITES_FILE
from src.automator import WindowAutomator # <-- Added this import

# Remove class-level patches
# @patch('src.app_logic.load_json_data')
# @patch('src.app_logic.get_item_categories') # Might need different mock for this logic
# @patch('src.app_logic.build_additem_command')
class TestAppLogic(unittest.TestCase):

    def setUp(self):
        # Mock the global automator instance used by app_logic
        self.automator_patcher = patch('src.app_logic.app.automator', spec=WindowAutomator)
        self.mock_automator = self.automator_patcher.start()
        # Mock the global game_found flag (though logic relies less on it now)
        self.game_found_patcher = patch('src.app_logic.app.game_found', True)
        self.mock_game_found = self.game_found_patcher.start()
        # Mock logging to suppress output during tests
        self.log_patcher = patch('src.app_logic.logging')
        self.mock_logging = self.log_patcher.start()

    def tearDown(self):
        self.automator_patcher.stop()
        self.game_found_patcher.stop()
        self.log_patcher.stop()

    # Test check_game_status_logic
    # No external mocks needed for this specific function test
    def test_check_game_status_logic_found(self):
        self.mock_game_found = True # Explicitly set for clarity
        result = app_logic.check_game_status_logic()
        self.assertEqual(result, {"status": "Game Found"})

    # No external mocks needed for this specific function test
    def test_check_game_status_logic_not_found(self):
        # Override patcher for this specific test case
        with patch('src.app_logic.app.game_found', False):
            result = app_logic.check_game_status_logic()
            self.assertEqual(result, {"status": "Game Not Found"})

    # Test run_single_command_logic
    # Only needs automator mock (provided by setUp)
    def test_run_single_command_logic_success(self):
        # Arrange
        test_command = " test_cmd "
        self.mock_automator.execute_command.return_value = True

        # Act
        result = app_logic.run_single_command_logic(test_command)

        # Assert
        self.assertEqual(result, {"success": True})
        self.mock_automator.execute_command.assert_called_once_with(test_command.strip(), verbose=False)

    # Only needs automator mock (provided by setUp)
    def test_run_single_command_logic_fail_exec(self):
        # Arrange
        test_command = "cmd"
        self.mock_automator.execute_command.return_value = False

        # Act
        result = app_logic.run_single_command_logic(test_command)

        # Assert
        # Updated Assertion: Expect message key
        self.assertFalse(result['success'])
        self.assertIn('message', result)
        self.assertIsInstance(result['message'], str)
        self.assertTrue(len(result['message']) > 0)
        self.mock_automator.execute_command.assert_called_once_with(test_command, verbose=False)

    # Only needs automator mock (provided by setUp)
    def test_run_single_command_logic_game_not_found(self):
         # Arrange
         # Simulate automator failing because game isn't found
         test_command = "cmd"
         self.mock_automator.execute_command.return_value = False
 
         # Act
         result = app_logic.run_single_command_logic(test_command)
 
         # Assert
         # Expect the standard failure message when execute_command fails
         self.assertFalse(result['success'])
         self.assertIn('message', result)
         self.assertIn('Failed to execute command', result['message'])
         self.mock_automator.execute_command.assert_called_once_with(test_command, verbose=False)

    # Only needs automator mock (provided by setUp)
    def test_run_single_command_logic_invalid_command(self):
        # Arrange
        test_command = None

        # Act
        result = app_logic.run_single_command_logic(test_command)

        # Assert
        self.assertEqual(result, {"success": False, "message": "Invalid command"})
        self.mock_automator.execute_command.assert_not_called()

    # Test get_presets_logic
    @patch('src.app_logic.load_json_data') # Mock only what's needed
    def test_get_presets_logic_success(self, mock_load_json):
        mock_load_json.return_value = {"Preset A": [], "Preset B": []}
        result = app_logic.get_presets_logic("battle")
        mock_load_json.assert_called_once_with("battles.json")
        self.assertEqual(result, {"presets": ["Preset A", "Preset B"]})

    @patch('src.app_logic.load_json_data') # Mock only what's needed
    def test_get_presets_logic_fail_load(self, mock_load_json):
        mock_load_json.return_value = None
        result = app_logic.get_presets_logic("battle")
        self.assertEqual(result, {"presets": []})

    # Test run_command_sequence_logic
    # Needs automator mock (setUp) and time.sleep mock
    @patch('src.app_logic.time.sleep') # Mock sleep to speed up test
    def test_run_command_sequence_logic_success(self, mock_sleep):
        commands = ["cmd1", "cmd2"]
        self.mock_automator.open_console.return_value = True
        self.mock_automator.execute_command_in_console.return_value = True
        self.mock_automator.close_console.return_value = True
        
        result = app_logic.run_command_sequence_logic(commands, "test_seq")
        
        self.assertEqual(result, {"success": True})
        self.mock_automator.open_console.assert_called_once_with(verbose=False)
        self.mock_automator.execute_command_in_console.assert_has_calls([
            call("cmd1", verbose=False),
            call("cmd2", verbose=False)
        ])
        self.mock_automator.close_console.assert_called_once_with(verbose=False)

    # Needs automator mock (setUp) and time.sleep mock
    @patch('src.app_logic.time.sleep') 
    def test_run_command_sequence_logic_fail_open(self, mock_sleep):
        self.mock_automator.open_console.return_value = False
        result = app_logic.run_command_sequence_logic(["cmd1"], "test_seq")
        # Updated Assertion: Expect message key
        self.assertFalse(result['success'])
        self.assertIn('message', result)
        self.assertIn('failed during test_seq', result['message'])
        self.mock_automator.execute_command_in_console.assert_not_called()
        self.mock_automator.close_console.assert_not_called()

    # Needs automator mock (setUp) and time.sleep mock
    @patch('src.app_logic.time.sleep') 
    def test_run_command_sequence_logic_fail_exec(self, mock_sleep):
        commands = ["cmd1", "cmd2"]
        self.mock_automator.open_console.return_value = True
        # Fail on the second command
        self.mock_automator.execute_command_in_console.side_effect = [True, False]
        self.mock_automator.close_console.return_value = True # Assume close succeeds

        result = app_logic.run_command_sequence_logic(commands, "test_seq")
        
        # Updated Assertion: Expect message key
        self.assertFalse(result['success'])
        self.assertIn('message', result)
        self.assertIn('failed during test_seq', result['message'])
        self.mock_automator.open_console.assert_called_once_with(verbose=False)
        self.mock_automator.execute_command_in_console.assert_has_calls([
            call("cmd1", verbose=False),
            call("cmd2", verbose=False) # Still called before failure detected
        ])
        self.mock_automator.close_console.assert_called_once_with(verbose=False) # Close is still called

    # Test add_item_logic
    # Needs automator mock (setUp) and build_additem_command mock
    @patch('src.app_logic.build_additem_command')
    def test_add_item_logic_success(self, mock_builder):
        item_id = "item001"
        quantity = 5
        built_command = "player.additem item001 5"
        mock_builder.return_value = built_command
        self.mock_automator.execute_command.return_value = True

        result = app_logic.add_item_logic(item_id, quantity)

        mock_builder.assert_called_once_with(item_id, quantity)
        self.mock_automator.execute_command.assert_called_once_with(built_command, verbose=False)
        self.assertEqual(result, {"success": True, "command": built_command})

    # Needs automator mock (setUp) and build_additem_command mock
    @patch('src.app_logic.build_additem_command')
    def test_add_item_logic_invalid_qty(self, mock_builder):
        result = app_logic.add_item_logic("item001", 0)
        self.assertEqual(result, {"success": False, "message": "Invalid quantity"})
        result2 = app_logic.add_item_logic("item001", "abc")
        self.assertEqual(result2, {"success": False, "message": "Invalid quantity"})
        mock_builder.assert_not_called()
        self.mock_automator.execute_command.assert_not_called()

    # ... Add similar tests for run_preset_logic, get_item_categories_logic, get_items_in_category_logic ...

class TestAppLogicFavorites(unittest.TestCase):

    @patch('src.app_logic.load_json_data')
    def test_load_favorites_logic_success(self, mock_load):
        # Arrange
        mock_fav_data = [
            {"name": "Fav 1", "command": "cmd1", "type": "single"},
            {"name": "Fav 2", "command": "cmd2", "type": "additem"}
        ]
        mock_load.return_value = mock_fav_data

        # Act
        result = app_logic.load_favorites_logic()

        # Assert
        self.assertTrue(result['success'])
        self.assertEqual(result['favorites'], mock_fav_data)
        mock_load.assert_called_once_with(data_loader.FAVORITES_FILE)

    @patch('src.app_logic.load_json_data')
    @patch('src.app_logic.save_json_data') # Mock save in case of reset
    def test_load_favorites_logic_not_list(self, mock_save, mock_load):
        # Arrange
        mock_load.return_value = {"not": "a list"} # Simulate corrupted file
        mock_save.return_value = True # Assume reset save succeeds
        
        # Act
        result = app_logic.load_favorites_logic()
        
        # Assert
        self.assertTrue(result['success'])
        self.assertEqual(result['favorites'], []) # Should return empty list
        mock_load.assert_called_once_with(data_loader.FAVORITES_FILE)
        mock_save.assert_called_once_with(data_loader.FAVORITES_FILE, []) # Check it saved the reset
        # Could also check logging.warning was called if logging is mocked
        
    @patch('src.app_logic.load_json_data')
    def test_load_favorites_logic_load_fails(self, mock_load):
        # Arrange
        mock_load.return_value = None # Simulate load error
        
        # Act
        result = app_logic.load_favorites_logic()
        
        # Assert
        self.assertTrue(result['success'])
        self.assertEqual(result['favorites'], []) # Should return empty list on error
        mock_load.assert_called_once_with(data_loader.FAVORITES_FILE)

    @patch('src.app_logic.load_json_data')
    @patch('src.app_logic.save_json_data')
    def test_save_favorite_logic_success(self, mock_save, mock_load):
        # Arrange
        mock_load.return_value = [] # Start with empty list
        mock_save.return_value = True
        fav_name = "My New Fav"
        fav_cmd = "tgm"
        fav_type = "single"
        expected_save_data = [{
            "name": fav_name,
            "command": fav_cmd,
            "type": fav_type
        }]
        
        # Act
        result = app_logic.save_favorite_logic(fav_name, fav_cmd, fav_type)
        
        # Assert
        self.assertEqual(result['status'], "success")
        self.assertIn("saved successfully", result['message'])
        mock_load.assert_called_once()
        mock_save.assert_called_once_with(data_loader.FAVORITES_FILE, expected_save_data)

    @patch('src.app_logic.load_json_data')
    @patch('src.app_logic.save_json_data')
    def test_save_favorite_logic_name_exists(self, mock_save, mock_load):
        # Arrange
        fav_name = "Existing Fav"
        existing_favs = [{
            "name": fav_name,
            "command": "old_cmd",
            "type": "single"
        }]
        mock_load.return_value = existing_favs
        
        # Act
        result = app_logic.save_favorite_logic(fav_name, "new_cmd", "single")
        
        # Assert
        self.assertEqual(result['status'], "exists")
        self.assertIn("already exists", result['message'])
        mock_load.assert_called_once()
        mock_save.assert_not_called() # Should not save if name exists

    def test_save_favorite_logic_empty_name(self):
        # Act
        result = app_logic.save_favorite_logic(" ", "cmd", "single")
        # Assert
        self.assertEqual(result['status'], "error")
        self.assertIn("cannot be empty", result['message'])

    @patch('src.app_logic.load_json_data')
    @patch('src.app_logic.save_json_data')
    def test_save_favorite_logic_save_fails(self, mock_save, mock_load):
        # Arrange
        mock_load.return_value = []
        mock_save.return_value = False # Simulate save failure
        
        # Act
        result = app_logic.save_favorite_logic("Fav Name", "cmd", "single")
        
        # Assert
        self.assertEqual(result['status'], "error")
        self.assertIn("Failed to save", result['message'])
        mock_load.assert_called_once()
        mock_save.assert_called_once() # Save was attempted

    @patch('src.app_logic.load_json_data')
    @patch('src.app_logic.save_json_data')
    def test_delete_favorite_logic_success(self, mock_save, mock_load):
        # Arrange
        fav_to_delete = "Delete Me"
        initial_favs = [
            {"name": "Keep Me", "command": "cmd1", "type": "single"},
            {"name": fav_to_delete, "command": "cmd2", "type": "additem"}
        ]
        expected_saved_favs = [
            {"name": "Keep Me", "command": "cmd1", "type": "single"}
        ]
        mock_load.return_value = initial_favs
        mock_save.return_value = True
        
        # Act
        result = app_logic.delete_favorite_logic(fav_to_delete)
        
        # Assert
        self.assertTrue(result['success'])
        self.assertIn("deleted successfully", result['message'])
        mock_load.assert_called_once()
        mock_save.assert_called_once_with(data_loader.FAVORITES_FILE, expected_saved_favs)

    @patch('src.app_logic.load_json_data')
    @patch('src.app_logic.save_json_data')
    def test_delete_favorite_logic_not_found(self, mock_save, mock_load):
        # Arrange
        initial_favs = [
            {"name": "Keep Me", "command": "cmd1", "type": "single"}
        ]
        mock_load.return_value = initial_favs
        
        # Act
        result = app_logic.delete_favorite_logic("Does Not Exist")
        
        # Assert
        self.assertFalse(result['success'])
        self.assertIn("not found", result['message'])
        mock_load.assert_called_once()
        mock_save.assert_not_called()
        
    @patch('src.app_logic.load_json_data')
    @patch('src.app_logic.save_json_data')
    def test_delete_favorite_logic_save_fails(self, mock_save, mock_load):
        # Arrange
        fav_to_delete = "Delete Me"
        initial_favs = [{"name": fav_to_delete, "command": "cmd2", "type": "additem"}]
        mock_load.return_value = initial_favs
        mock_save.return_value = False # Simulate save failure
        
        # Act
        result = app_logic.delete_favorite_logic(fav_to_delete)
        
        # Assert
        self.assertFalse(result['success'])
        self.assertIn("Failed to save", result['message'])
        mock_load.assert_called_once()
        mock_save.assert_called_once() # Save was attempted
        
    @patch('src.app_logic.load_favorites_logic')
    @patch('src.app_logic.run_single_command_logic')
    def test_run_favorite_logic_success(self, mock_run_single, mock_load_favs):
        # Arrange
        fav_name = "Run Me"
        fav_cmd = "tgm"
        favs = [{"name": fav_name, "command": fav_cmd, "type": "single"}]
        mock_load_favs.return_value = {"success": True, "favorites": favs}
        mock_run_single.return_value = {"success": True, "message": "Command executed"} # Simulate success
        
        # Act
        result = app_logic.run_favorite_logic(fav_name)
        
        # Assert
        self.assertTrue(result['success'])
        self.assertIn(f"Ran favorite '{fav_name}'", result['message']) 
        mock_load_favs.assert_called_once()
        mock_run_single.assert_called_once_with(fav_cmd)

    @patch('src.app_logic.load_favorites_logic')
    @patch('src.app_logic.run_single_command_logic')
    def test_run_favorite_logic_not_found(self, mock_run_single, mock_load_favs):
        # Arrange
        mock_load_favs.return_value = {"success": True, "favorites": []} # No favorites
        
        # Act
        result = app_logic.run_favorite_logic("Not Found")
        
        # Assert
        self.assertFalse(result['success'])
        self.assertIn("not found", result['message'])
        mock_load_favs.assert_called_once()
        mock_run_single.assert_not_called()
        
    @patch('src.app_logic.load_favorites_logic')
    @patch('src.app_logic.run_single_command_logic')
    def test_run_favorite_logic_command_fails(self, mock_run_single, mock_load_favs):
        # Arrange
        fav_name = "Fail Me"
        fav_cmd = "badcmd"
        favs = [{"name": fav_name, "command": fav_cmd, "type": "single"}]
        mock_load_favs.return_value = {"success": True, "favorites": favs}
        mock_run_single.return_value = {"success": False, "message": "Execution failed"} # Simulate failure
        
        # Act
        result = app_logic.run_favorite_logic(fav_name)
        
        # Assert
        self.assertFalse(result['success'])
        self.assertIn(f"Ran favorite '{fav_name}'", result['message']) 
        self.assertIn("Execution failed", result['message']) 
        mock_load_favs.assert_called_once()
        mock_run_single.assert_called_once_with(fav_cmd)
        
# You would typically have other test classes for other logic functions here
# class TestAppLogicOther(...):
#     ...
        
if __name__ == '__main__':
    # Create a dummy test suite if this is the only test file, 
    # otherwise integrate into a larger test runner
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestAppLogic))
    suite.addTest(unittest.makeSuite(TestAppLogicFavorites))
    # Add other test classes here: suite.addTest(unittest.makeSuite(TestAppLogicOther))
    runner = unittest.TextTestRunner()
    runner.run(suite) 