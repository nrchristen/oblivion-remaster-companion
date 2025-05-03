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

# Mock the lower level modules it calls
# We mock the functions/classes within the module *where they are looked up*
@patch('src.app_logic.load_json_data')
@patch('src.app_logic.get_item_categories')
@patch('src.app_logic.build_additem_command')
class TestAppLogic(unittest.TestCase):

    def setUp(self):
        # Create a mock automator instance for each test
        self.mock_automator = MagicMock()
        # Patch the global automator instance used by app_logic
        self.automator_patcher = patch('app.automator', self.mock_automator)
        self.automator_patcher.start()
        # Patch the global game_found state
        self.game_found_patcher = patch('app.game_found', True) # Assume game found by default
        self.mock_game_found = self.game_found_patcher.start()

    def tearDown(self):
        self.automator_patcher.stop()
        self.game_found_patcher.stop()

    # Test check_game_status_logic
    def test_check_game_status_logic_found(self, mock_builder, mock_get_cats, mock_load_json):
        self.mock_game_found = True # Already set in setup, but explicit is fine
        result = app_logic.check_game_status_logic()
        self.assertEqual(result, {"status": "Game Found"})

    def test_check_game_status_logic_not_found(self, mock_builder, mock_get_cats, mock_load_json):
        app.game_found = False # Override patch for this test
        result = app_logic.check_game_status_logic()
        self.assertEqual(result, {"status": "Game Not Found"})

    # Test run_single_command_logic
    def test_run_single_command_logic_success(self, mock_builder, mock_get_cats, mock_load_json):
        self.mock_automator.execute_command.return_value = True
        command = " test_cmd "
        result = app_logic.run_single_command_logic(command)
        self.mock_automator.execute_command.assert_called_once_with("test_cmd", verbose=False)
        self.assertEqual(result, {"success": True})

    def test_run_single_command_logic_fail_exec(self, mock_builder, mock_get_cats, mock_load_json):
        self.mock_automator.execute_command.return_value = False
        result = app_logic.run_single_command_logic("cmd")
        self.assertEqual(result, {"success": False})

    def test_run_single_command_logic_game_not_found(self, mock_builder, mock_get_cats, mock_load_json):
        app.game_found = False
        result = app_logic.run_single_command_logic("cmd")
        self.assertEqual(result, {"success": False, "message": "Game not found"})
        self.mock_automator.execute_command.assert_not_called()
        
    def test_run_single_command_logic_invalid_cmd(self, mock_builder, mock_get_cats, mock_load_json):
        result = app_logic.run_single_command_logic(None)
        self.assertEqual(result, {"success": False, "message": "Invalid command"})
        self.mock_automator.execute_command.assert_not_called()

    # Test get_presets_logic
    def test_get_presets_logic_success(self, mock_builder, mock_get_cats, mock_load_json):
        mock_load_json.return_value = {"Preset A": [], "Preset B": []}
        result = app_logic.get_presets_logic("battle")
        mock_load_json.assert_called_once_with("battles.json")
        self.assertEqual(result, {"presets": ["Preset A", "Preset B"]})

    def test_get_presets_logic_fail_load(self, mock_builder, mock_get_cats, mock_load_json):
        mock_load_json.return_value = None
        result = app_logic.get_presets_logic("battle")
        self.assertEqual(result, {"presets": []})

    # Test run_command_sequence_logic
    @patch('src.app_logic.time.sleep') # Mock sleep to speed up test
    def test_run_command_sequence_logic_success(self, mock_sleep, mock_builder, mock_get_cats, mock_load_json):
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

    @patch('src.app_logic.time.sleep') 
    def test_run_command_sequence_logic_fail_open(self, mock_sleep, mock_builder, mock_get_cats, mock_load_json):
        self.mock_automator.open_console.return_value = False
        result = app_logic.run_command_sequence_logic(["cmd1"], "test_seq")
        self.assertEqual(result, {"success": False})
        self.mock_automator.execute_command_in_console.assert_not_called()
        self.mock_automator.close_console.assert_not_called()

    @patch('src.app_logic.time.sleep') 
    def test_run_command_sequence_logic_fail_exec(self, mock_sleep, mock_builder, mock_get_cats, mock_load_json):
        commands = ["cmd1", "cmd2"]
        self.mock_automator.open_console.return_value = True
        # Fail on the second command
        self.mock_automator.execute_command_in_console.side_effect = [True, False]
        self.mock_automator.close_console.return_value = True

        result = app_logic.run_command_sequence_logic(commands, "test_seq")
        
        self.assertEqual(result, {"success": False})
        self.mock_automator.open_console.assert_called_once_with(verbose=False)
        self.mock_automator.execute_command_in_console.assert_has_calls([
            call("cmd1", verbose=False),
            call("cmd2", verbose=False) # Still called before failure detected
        ])
        self.mock_automator.close_console.assert_called_once_with(verbose=False) # Close is still called

    # Test add_item_logic
    def test_add_item_logic_success(self, mock_builder, mock_get_cats, mock_load_json):
        item_id = "item001"
        quantity = 5
        built_command = "player.additem item001 5"
        mock_builder.return_value = built_command
        self.mock_automator.execute_command.return_value = True

        result = app_logic.add_item_logic(item_id, quantity)

        mock_builder.assert_called_once_with(item_id, quantity)
        self.mock_automator.execute_command.assert_called_once_with(built_command, verbose=False)
        self.assertEqual(result, {"success": True})

    def test_add_item_logic_invalid_qty(self, mock_builder, mock_get_cats, mock_load_json):
        result = app_logic.add_item_logic("item001", 0)
        self.assertEqual(result, {"success": False, "message": "Invalid quantity"})
        result2 = app_logic.add_item_logic("item001", "abc")
        self.assertEqual(result2, {"success": False, "message": "Invalid quantity"})
        mock_builder.assert_not_called()
        self.mock_automator.execute_command.assert_not_called()

    # ... Add similar tests for run_preset_logic, get_item_categories_logic, get_items_in_category_logic ...

if __name__ == '__main__':
    unittest.main() 