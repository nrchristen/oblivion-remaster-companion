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
from app_logic import (
    # ... other functions ...
    add_item_logic,
    get_npcs_logic,
    save_battle_preset_logic,
    load_favorites_logic,
    save_favorite_logic,
    delete_favorite_logic,
    run_favorite_logic,
    # Add new location functions
    get_location_categories_logic,
    get_locations_in_category_logic,
    teleport_to_location_logic 
)

# Mock the global automator instance used by app_logic
# Use autospec=True to ensure the mock has the same methods/attributes
mock_automator_instance = MagicMock(spec=WindowAutomator)

# --- Test Data ---
MOCK_LOCATION_CATEGORIES = {
    "Cities": "locations/cities.json",
    "Guild Halls": "locations/guilds.json"
}
MOCK_CITY_LOCATIONS = {
    "Anvil": "AnvilCity",
    "Bravil": "BravilCity"
}

# Remove class-level patches
# @patch('src.app_logic.load_json_data')
# @patch('src.app_logic.get_item_categories') # Might need different mock for this logic
# @patch('src.app_logic.build_additem_command')
class TestAppLogic(unittest.TestCase):

    def setUp(self):
        # Mock the global automator instance used by app_logic
        self.automator_patcher = patch('src.app_logic.app.automator', spec=WindowAutomator)
        self.mock_automator = self.automator_patcher.start()
        # Remove patching of the non-existent game_found flag
        # self.game_found_patcher = patch('src.app_logic.app.game_found', True)
        # self.mock_game_found = self.game_found_patcher.start()
        # Mock logging to suppress output during tests
        self.log_patcher = patch('src.app_logic.logging')
        self.mock_logging = self.log_patcher.start()
        # Mock data loader functions used by various logic functions
        self.load_json_patcher = patch('src.app_logic.load_json_data')
        self.mock_load_json = self.load_json_patcher.start()
        self.save_json_patcher = patch('src.app_logic.save_json_data')
        self.mock_save_json = self.save_json_patcher.start()
        # Set default mock automator state (game found initially)
        self.mock_automator.hwnd = 12345 # Simulate found window
        self.mock_automator.is_in_debug_mode.return_value = False
        self.mock_automator.get_debug_filepath.return_value = None

    def tearDown(self):
        self.automator_patcher.stop()
        # self.game_found_patcher.stop() # Removed
        self.log_patcher.stop()
        self.load_json_patcher.stop()
        self.save_json_patcher.stop()

    # Test check_game_status_logic
    def test_check_game_status_logic_found(self):
        # Arrange: Automator has HWND, not in debug mode (default setUp state)
        self.mock_automator.hwnd = 12345
        self.mock_automator.is_in_debug_mode.return_value = False
        # Act
        result = app_logic.check_game_status_logic()
        # Assert
        self.assertEqual(result, {"status": "Game Found"})

    def test_check_game_status_logic_not_found(self):
        # Arrange: Automator has no HWND, not in debug mode
        self.mock_automator.hwnd = None
        self.mock_automator.is_in_debug_mode.return_value = False
        # Act
        result = app_logic.check_game_status_logic()
        # Assert
        self.assertEqual(result, {"status": "Game Not Found"})

    def test_check_game_status_logic_debug_mode(self):
        # Arrange: Automator has no HWND, is in debug mode
        self.mock_automator.hwnd = None
        self.mock_automator.is_in_debug_mode.return_value = True
        self.mock_automator.get_debug_filepath.return_value = "C:\\path\\to\\debug_companion_123.txt"
        # Act
        result = app_logic.check_game_status_logic()
        # Assert
        self.assertEqual(result, {"status": "Debug Mode Active (debug_companion_123.txt)"})

    # Test run_single_command_logic
    def test_run_single_command_logic_success(self):
        # Arrange: Game found, command execution succeeds
        self.mock_automator.execute_command.return_value = True
        self.mock_automator.is_in_debug_mode.return_value = False # Ensure not in debug mode
        command = "player.additem f 100"
        # Act
        result = app_logic.run_single_command_logic(command)
        # Assert
        self.assertEqual(result, {"success": True})
        self.mock_automator.execute_command.assert_called_once_with(command, verbose=False)

    def test_run_single_command_logic_fail_exec(self):
        # Arrange: Game found, command execution fails
        self.mock_automator.execute_command.return_value = False
        self.mock_automator.is_in_debug_mode.return_value = False
        command = "player.additem f 100"
        # Act
        result = app_logic.run_single_command_logic(command)
        # Assert
        self.assertEqual(result, {"success": False, "message": "Failed to execute command. Check log or ensure game is focused."}) # Updated message
        self.mock_automator.execute_command.assert_called_once_with(command, verbose=False)

    def test_run_single_command_logic_debug_mode_exec(self):
        # Arrange: Game not found, automator enters debug mode and logs successfully
        # execute_command should return True when logging in debug mode
        self.mock_automator.execute_command.return_value = True
        self.mock_automator.is_in_debug_mode.return_value = True # Check this AFTER execute_command returns
        command = "player.additem f 100"
        # Act
        result = app_logic.run_single_command_logic(command)
        # Assert
        # Even though execute_command returned True (for logging), the logic layer should still report success True
        self.assertEqual(result, {"success": True})
        self.mock_automator.execute_command.assert_called_once_with(command, verbose=False)

    def test_run_single_command_logic_debug_mode_fail_log(self):
        # Arrange: Game not found, automator enters debug mode but logging fails
        # execute_command should return False if logging fails in debug mode (e.g., setup failed)
        self.mock_automator.execute_command.return_value = False
        self.mock_automator.is_in_debug_mode.return_value = True # Check this AFTER execute_command returns
        command = "player.additem f 100"
        # Act
        result = app_logic.run_single_command_logic(command)
        # Assert
        # If execute_command returns False while in debug mode, the logic layer reports failure
        self.assertEqual(result, {"success": False, "message": "Command logged to debug file. Game not found."}) # Updated message
        self.mock_automator.execute_command.assert_called_once_with(command, verbose=False)


    def test_run_single_command_logic_invalid_command(self):
        # Arrange: Command is invalid (None)
        # Act
        result = app_logic.run_single_command_logic(None)
        # Assert
        self.assertEqual(result, {"success": False, "message": "Invalid command"})
        self.mock_automator.execute_command.assert_not_called()

    # Test get_presets_logic
    @patch('src.app_logic.load_json_data')
    def test_get_presets_logic_success(self, mock_load):
        # Arrange
        mock_load.return_value = {"Preset1": ["cmd1"], "Preset2": ["cmd2"]}
        # Act
        result = app_logic.get_presets_logic("test_type")
        # Assert
        self.assertEqual(result, {"presets": ["Preset1", "Preset2"]})
        mock_load.assert_called_once_with("test_types.json")

    @patch('src.app_logic.load_json_data')
    def test_get_presets_logic_fail_load(self, mock_load):
        # Arrange
        mock_load.return_value = None
        # Act
        result = app_logic.get_presets_logic("test_type")
        # Assert
        self.assertEqual(result, {"presets": []})
        mock_load.assert_called_once_with("test_types.json")

    # Test run_command_sequence_logic
    def test_run_command_sequence_logic_success(self):
        # Arrange: Game found, all commands succeed
        self.mock_automator.open_console.return_value = True
        self.mock_automator.execute_command_in_console.return_value = True
        self.mock_automator.close_console.return_value = True
        self.mock_automator.is_in_debug_mode.return_value = False
        commands = ["cmd1", "cmd2"]
        # Act
        result = app_logic.run_command_sequence_logic(commands, "test_seq")
        # Assert
        self.assertEqual(result, {"success": True})
        self.mock_automator.open_console.assert_called_once_with(verbose=False)
        self.mock_automator.execute_command_in_console.assert_has_calls([
            call("cmd1", verbose=False),
            call("cmd2", verbose=False)
        ])
        self.mock_automator.close_console.assert_called_once_with(verbose=False)

    def test_run_command_sequence_logic_fail_open(self):
        # Arrange: Game found, but opening console fails
        self.mock_automator.open_console.return_value = False
        self.mock_automator.is_in_debug_mode.return_value = False # Assume it didn't enter debug
        commands = ["cmd1", "cmd2"]
        # Act
        result = app_logic.run_command_sequence_logic(commands, "test_seq")
        # Assert
        self.assertEqual(result, {"success": False, "message": "One or more commands failed during test_seq execution."})
        self.mock_automator.open_console.assert_called_once_with(verbose=False)
        self.mock_automator.execute_command_in_console.assert_not_called()
        self.mock_automator.close_console.assert_not_called()

    def test_run_command_sequence_logic_fail_exec(self):
        # Arrange: Game found, open succeeds, but one command fails
        self.mock_automator.open_console.return_value = True
        self.mock_automator.execute_command_in_console.side_effect = [True, False] # Second command fails
        self.mock_automator.close_console.return_value = True # Close still called
        self.mock_automator.is_in_debug_mode.return_value = False
        commands = ["cmd1", "cmd2"]
        # Act
        result = app_logic.run_command_sequence_logic(commands, "test_seq")
        # Assert
        self.assertEqual(result, {"success": False, "message": "One or more commands failed during test_seq execution."})
        self.mock_automator.open_console.assert_called_once_with(verbose=False)
        self.mock_automator.execute_command_in_console.assert_has_calls([
            call("cmd1", verbose=False),
            call("cmd2", verbose=False)
        ])
        self.mock_automator.close_console.assert_called_once_with(verbose=False)

    def test_run_command_sequence_debug_mode(self):
         # Arrange: Automator starts in debug mode
        self.mock_automator.is_in_debug_mode.return_value = True
        self.mock_automator.open_console.return_value = True # Simulates logging success
        self.mock_automator.execute_command_in_console.return_value = True # Simulates logging success
        self.mock_automator.close_console.return_value = True # Simulates logging success
        commands = ["cmd1", "cmd2"]
        # Act
        result = app_logic.run_command_sequence_logic(commands, "test_seq")
        # Assert
        self.assertEqual(result, {"success": True}) # Overall sequence reports success (logging worked)
        self.mock_automator.open_console.assert_called_once_with(verbose=False)
        self.mock_automator.execute_command_in_console.assert_has_calls([
            call("cmd1", verbose=False),
            call("cmd2", verbose=False)
        ])
        self.mock_automator.close_console.assert_called_once_with(verbose=False)


    # Test add_item_logic
    @patch('src.app_logic.build_additem_command')
    def test_add_item_logic_success(self, mock_build):
        # Arrange: Game found, command builds and executes successfully
        self.mock_automator.execute_command.return_value = True
        self.mock_automator.is_in_debug_mode.return_value = False
        mock_build.return_value = "player.additem 123 5"
        # Act
        result = app_logic.add_item_logic("123", 5)
        # Assert
        self.assertEqual(result, {"success": True, "command": "player.additem 123 5"})
        mock_build.assert_called_once_with("123", 5)
        self.mock_automator.execute_command.assert_called_once_with("player.additem 123 5", verbose=False)

    def test_add_item_logic_invalid_qty(self):
        # Arrange
        # Act
        result_zero = app_logic.add_item_logic("123", 0)
        result_neg = app_logic.add_item_logic("123", -1)
        result_str = app_logic.add_item_logic("123", "abc")
        # Assert
        self.assertEqual(result_zero, {"success": False, "message": "Quantity must be positive"})
        self.assertEqual(result_neg, {"success": False, "message": "Quantity must be positive"})
        self.assertEqual(result_str, {"success": False, "message": "Invalid quantity"})
        self.mock_automator.execute_command.assert_not_called()

    # ... other test methods remain the same, assuming they don't directly rely on game_found ...

    # Example for favorite logic tests (needs mocking load/save)
    def test_save_favorite_logic_success(self):
        # Arrange
        self.mock_load_json.return_value = [] # Start with empty favorites
        self.mock_save_json.return_value = True
        # Act
        result = app_logic.save_favorite_logic("Fav Name", "cmd", "type")
        # Assert
        self.assertEqual(result['status'], "success")
        self.mock_load_json.assert_called_once_with(data_loader.FAVORITES_FILE)
        self.mock_save_json.assert_called_once_with(data_loader.FAVORITES_FILE, [{'name': 'Fav Name', 'command': 'cmd', 'type': 'type'}])

    def test_save_favorite_logic_exists(self):
        # Arrange
        self.mock_load_json.return_value = [{'name': 'Fav Name', 'command': 'old_cmd', 'type': 'old_type'}]
        # Act
        result = app_logic.save_favorite_logic("Fav Name", "new_cmd", "new_type")
        # Assert
        self.assertEqual(result['status'], "exists")
        self.mock_load_json.assert_called_once_with(data_loader.FAVORITES_FILE)
        self.mock_save_json.assert_not_called()

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