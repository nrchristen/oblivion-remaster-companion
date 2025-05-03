import unittest
from unittest.mock import patch, MagicMock, call
import os
import sys

# Ensure src is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src import ui
from src.ui import (
    _get_numeric_input,
    _select_from_list,
    handle_preset_battle_selection,
    handle_battle_mode_entry,
    GO_BACK
)

class TestUiHelpers(unittest.TestCase):

    @patch('builtins.input')
    def test_get_numeric_input_valid(self, mock_input):
        mock_input.return_value = "123"
        result = _get_numeric_input("Enter num: ")
        self.assertEqual(result, 123)

    @patch('builtins.input')
    @patch('builtins.print') # Suppress error print
    def test_get_numeric_input_invalid_then_valid(self, mock_print, mock_input):
        mock_input.side_effect = ["abc", " ", "42"]
        result = _get_numeric_input("Enter num: ")
        self.assertEqual(result, 42)
        self.assertEqual(mock_input.call_count, 3)
        # Check if print was called for the invalid inputs
        self.assertGreaterEqual(mock_print.call_count, 2) 

    @patch('builtins.input')
    @patch('builtins.print') # Suppress error print
    def test_get_numeric_input_range_check(self, mock_print, mock_input):
        mock_input.side_effect = ["0", "11", "5"] # Below min, above max, then valid
        result = _get_numeric_input("Enter num: ", min_val=1, max_val=10)
        self.assertEqual(result, 5)
        self.assertEqual(mock_input.call_count, 3)
        self.assertGreaterEqual(mock_print.call_count, 2)

    @patch('builtins.input')
    def test_get_numeric_input_zero_allowed(self, mock_input):
        mock_input.return_value = "0"
        result = _get_numeric_input("Enter num: ", allow_zero=True)
        self.assertEqual(result, 0)

    @patch('builtins.input')
    @patch('builtins.print') # Suppress error print
    def test_get_numeric_input_zero_not_allowed(self, mock_print, mock_input):
        mock_input.side_effect = ["0", "1"]
        result = _get_numeric_input("Enter num: ", allow_zero=False) # Default
        self.assertEqual(result, 1)
        self.assertGreaterEqual(mock_print.call_count, 1)

    @patch('src.ui.pick.pick')
    @patch('src.ui.clear_screen') # Mock to avoid side effects
    @patch('builtins.print') # Mock to suppress '--> Selected'
    def test_select_from_list_select_item(self, mock_print, mock_clear, mock_pick):
        items = ["Apple", ("Banana", "B001")]
        prompt_text = "Fruit"
        # Simulate selecting the second item (Banana)
        mock_pick.return_value = ("Banana (ID: B001)", 2) # pick returns (display_name, index)

        result = _select_from_list(items, prompt_text)

        expected_options = [
            ("Go Back", GO_BACK),
            ("Apple", "Apple"),
            ("Banana (ID: B001)", ("Banana", "B001"))
        ]
        mock_pick.assert_called_once()
        # Check that the first arg to pick was the list of display names
        self.assertEqual(mock_pick.call_args[0][0], [opt[0] for opt in expected_options])
        self.assertEqual(result, ("Banana", "B001")) # Should return the original value

    @patch('src.ui.pick.pick')
    @patch('src.ui.clear_screen')
    def test_select_from_list_go_back(self, mock_clear, mock_pick):
        items = ["Apple"]
        prompt_text = "Fruit"
        # Simulate selecting the first item, which is "Go Back"
        mock_pick.return_value = ("Go Back", 0)
        
        result = _select_from_list(items, prompt_text)
        self.assertIs(result, GO_BACK)

    @patch('src.ui.pick.pick', side_effect=KeyboardInterrupt)
    @patch('src.ui.clear_screen')
    def test_select_from_list_keyboard_interrupt(self, mock_clear, mock_pick):
        items = ["Apple"]
        prompt_text = "Fruit"
        result = _select_from_list(items, prompt_text)
        self.assertIs(result, GO_BACK)

class TestBattleModeUI(unittest.TestCase):

    @patch('src.ui.data_loader.load_json_data')
    @patch('src.ui._select_from_list')
    @patch('builtins.print') # Suppress info prints
    def test_handle_preset_battle_selection_success(self, mock_print, mock_select, mock_load):
        presets = {"Battle A": ["cmdA1"], "Battle B": ["cmdB1"]}
        mock_load.return_value = presets
        mock_select.return_value = "Battle A" # Simulate selecting the name

        result = handle_preset_battle_selection()

        mock_load.assert_called_once_with("battles.json")
        mock_select.assert_called_once_with(list(presets.keys()), "Preset Battle")
        self.assertEqual(result, ["cmdA1"])

    @patch('src.ui.data_loader.load_json_data')
    @patch('src.ui._select_from_list')
    @patch('builtins.print') 
    def test_handle_preset_battle_selection_go_back(self, mock_print, mock_select, mock_load):
        mock_load.return_value = {"Battle A": []}
        mock_select.return_value = GO_BACK # Simulate selecting Go Back
        
        result = handle_preset_battle_selection()
        self.assertIsNone(result)

    @patch('src.ui.data_loader.load_json_data', return_value=None)
    @patch('builtins.print')
    @patch('builtins.input') # Mock the input pause
    def test_handle_preset_battle_selection_load_fail(self, mock_input, mock_print, mock_load):
        result = handle_preset_battle_selection()
        self.assertIsNone(result)
        mock_print.assert_any_call("Error: Could not load battle presets from data/battles.json")

    @patch('src.ui.pick.pick')
    @patch('src.ui.handle_preset_battle_selection')
    @patch('src.ui.handle_battle_stage')
    @patch('src.ui.clear_screen')
    def test_handle_battle_mode_entry_preset(self, mock_clear, mock_stage, mock_preset, mock_pick):
        mock_pick.return_value = ("Select Preset Battle", 0) # Index 0 corresponds to preset
        mock_preset.return_value = ["preset_cmd"]
        
        result = handle_battle_mode_entry()
        
        self.assertEqual(result, ["preset_cmd"])
        mock_preset.assert_called_once()
        mock_stage.assert_not_called()

    @patch('src.ui.pick.pick')
    @patch('src.ui.handle_preset_battle_selection')
    @patch('src.ui.handle_battle_stage')
    @patch('src.ui.clear_screen')
    def test_handle_battle_mode_entry_custom(self, mock_clear, mock_stage, mock_preset, mock_pick):
        mock_pick.return_value = ("Custom Battle Setup", 1) # Index 1 corresponds to custom
        mock_stage.return_value = ["custom_cmd"]

        result = handle_battle_mode_entry()
        
        self.assertEqual(result, ["custom_cmd"])
        mock_stage.assert_called_once()
        mock_preset.assert_not_called()

    @patch('src.ui.pick.pick')
    @patch('src.ui.handle_preset_battle_selection')
    @patch('src.ui.handle_battle_stage')
    @patch('src.ui.clear_screen')
    def test_handle_battle_mode_entry_back(self, mock_clear, mock_stage, mock_preset, mock_pick):
        mock_pick.return_value = ("Go Back", 2) # Index 2 corresponds to back

        result = handle_battle_mode_entry()
        
        self.assertIsNone(result)
        mock_stage.assert_not_called()
        mock_preset.assert_not_called()

if __name__ == '__main__':
    unittest.main() 