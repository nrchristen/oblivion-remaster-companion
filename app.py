import webview
import argparse
import sys
import os
import platform
import logging
import traceback
import colorama
from colorama import Fore, Back, Style
import json

# Ensure src is importable (adjust path if necessary)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.automator import WindowAutomator
from src.data_loader import (
    load_json_data, 
    get_item_categories, 
    add_battle_preset,
    load_items_for_category,
    load_all_locations,
    save_json_data, # Assuming save_json_data is needed for favorites
    DATA_DIR,       # Assuming needed for favorites path
    FAVORITES_FILE,  # Assuming needed for favorites
    BATTLES_FILE
)
from src.command_builder import build_additem_command, build_placeatme_command
# Import the new logic layer
from src import app_logic 
# Import the new CLI entry point
from src.cli_ui import run_companion_cli
# Import the setup_logging function
from src.config import setup_logging
# from src.game_connector import GameConnector # Commented out - file missing

# --- Global Variables (Careful with state if making multi-threaded later) ---
TARGET_EXECUTABLE = "OblivionRemastered-WinGDK-Shipping.exe" # Or load from config
automator = WindowAutomator(TARGET_EXECUTABLE)
# game_found = False # Removed global - use automator state
# log_file = 'companion_log.txt' # Moved to config.py
window = None # Global reference to the pywebview window
# Removed stop_event
# stop_event = threading.Event() 

# Colorama Setup
COLOR_TEXT = Fore.YELLOW
COLOR_BG = Back.RED
COLOR_INDICATOR = Fore.LIGHTRED_EX
COLOR_RESET = Style.RESET_ALL
colorama.init(autoreset=True)

# --- Logging Setup ---
# Call the setup function from the config module
setup_logging()

# Initialize logging (ensure this is done early)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize Game Connector
# game_connector = GameConnector() # Commented out - class missing

# --- API Class for pywebview --- 
class Api:
    def __init__(self):
        self.item_categories = get_item_categories()
        self.all_locations = load_all_locations()
        # Load favorites on init too
        self.favorites = self._load_favorites_internal()

    def _load_favorites_internal(self):
        """Internal helper to load favorites."""
        favs = load_json_data(FAVORITES_FILE) 
        # Ensure it's a list, default to empty list if load fails or wrong type
        return favs if isinstance(favs, list) else []

    def check_status(self):
        """Checks if the game process/window is found or if in debug mode."""
        logging.info("API: check_status called.")
        result = app_logic.check_game_status_logic() 
        logging.info(f"API: check_status returning: {result}")
        return result

    def run_single_command(self, command):
        """Runs a single command using the automator."""
        if not command or not isinstance(command, str):
             logging.warning(f"Invalid command received: {command}")
             return {"success": False, "message": "Invalid command format."}
        
        logging.info(f"Running command: {command}")
        try:
            # Use WindowAutomator's execute_command method (correct name)
            # success, message = automator.run_command(command) # Old incorrect name
            success = automator.execute_command(command) # Call the correct method
            # The execute_command method now directly returns True/False 
            # and handles logging/messaging internally including debug mode messages.
            # We can simplify the API response based on this boolean.
            if success:
                 # Message is less important now as execute_command handles logging
                 logging.info(f"Command '{command}' execution cycle reported success.")
                 return {"success": True, "message": "Command sent (check game/log)."} 
            else:
                 # The reason for failure (game not found, exec failed, etc.) 
                 # should be logged by execute_command or its sub-methods.
                 logging.error(f"Command '{command}' execution cycle reported failure.")
                 return {"success": False, "message": "Command failed (check game/log)."}
        except Exception as e:
            logging.exception(f"Exception running command '{command}': {e}")
            return {"success": False, "message": f"Python error: {e}"}

    def get_battle_presets(self):
        """Loads and returns the list of battle preset names."""
        logging.info("API: get_battle_presets called.")
        result = app_logic.get_presets_logic("battle") # Delegate
        logging.info(f"API: get_battle_presets returning {len(result.get('presets',[]))} presets.")
        return result

    def run_preset_battle(self, preset_name):
        """Runs a sequence of commands from a named battle preset."""
        logging.info(f"API: run_preset_battle called for preset: '{preset_name}'")
        result = app_logic.run_preset_logic(preset_name, "battle") # Delegate
        logging.info(f"API: run_preset_battle result: {result}")
        return result

    # --- Item API Methods ---
    def get_item_categories_api(self):
        """Loads and returns item category names and filenames."""
        logging.info("API: get_item_categories_api called.")
        result = app_logic.get_item_categories_logic() # Delegate
        logging.info(f"API: get_item_categories_api returning {len(result.get('categories',{}))} categories.")
        return result

    def get_items_in_category(self, filename):
        """Loads items from a specific category file."""
        logging.info(f"API: get_items_in_category called for file: '{filename}'")
        result = app_logic.get_items_in_category_logic(filename) # Delegate
        logging.info(f"API: get_items_in_category returning {len(result.get('items',{}))} items.")
        return result

    def add_item(self, item_id, quantity):
        """Builds and executes the additem command."""
        logging.info(f"API: add_item called: ID={item_id}, Qty={quantity}")
        # Delegate to logic layer
        result = app_logic.add_item_logic(item_id, quantity)
        logging.info(f"API: add_item result: {result}")
        return result # Result now includes {"success": bool, "message": str, "command": str}

    # --- Custom Battle API Methods ---
    def get_npcs(self):
        logging.info("API: get_npcs called.")
        result = app_logic.get_npcs_logic()
        logging.info(f"API: get_npcs returning {len(result.get('npcs',{}))} NPCs.")
        return result

    def build_placeatme_command(self, npc_id, quantity):
        logging.info(f"API: build_placeatme_command called: ID={npc_id}, Qty={quantity}")
        # This one still has direct logic, add logging here
        try:
            qty = int(quantity)
            if qty <= 0: raise ValueError("Qty must be positive")
            command = build_placeatme_command(npc_id, qty)
            logging.info(f"API: build_placeatme_command successful: {command}")
            return {"success": True, "command": command}
        except Exception as e:
            logging.error(f"API: Error building placeatme command: {e}", exc_info=True)
            return {"success": False, "message": str(e)}

    def save_battle_preset(self, preset_name, command_list):
        logging.info(f"API: save_battle_preset called: Name='{preset_name}', Commands={len(command_list)}")
        result = app_logic.save_battle_preset_logic(preset_name, command_list)
        logging.info(f"API: save_battle_preset result: {result}")
        return result
        
    def run_custom_battle(self, command_list):
        logging.info(f"API: run_custom_battle called: Commands={len(command_list)}")
        result = app_logic.run_command_sequence_logic(command_list, "custom battle")
        logging.info(f"API: run_custom_battle result: {result}")
        return result

    # --- Favorites API Methods ---

    def get_favorites(self):
        """Loads and returns the list of favorite commands."""
        logging.info("API: get_favorites called.")
        result = app_logic.load_favorites_logic()
        logging.info(f"API: get_favorites returning {len(result.get('favorites',[]))} favorites.")
        return result

    def save_favorite(self, name, command, command_type):
        """Saves a command as a favorite."""
        logging.info(f"API: save_favorite called: Name='{name}', Type='{command_type}', Cmd=\"{command}\"")
        result = app_logic.save_favorite_logic(name, command, command_type)
        logging.info(f"API: save_favorite result: {result}")
        return result 

    def delete_favorite(self, name):
        """Deletes a favorite by name."""
        logging.info(f"API: delete_favorite called: Name='{name}'")
        result = app_logic.delete_favorite_logic(name)
        logging.info(f"API: delete_favorite result: {result}")
        return result
        
    def run_favorite(self, name):
        """Runs a favorite command by name."""
        logging.info(f"API: run_favorite called: Name='{name}'")
        result = app_logic.run_favorite_logic(name)
        logging.info(f"API: run_favorite result: {result}")
        return result

    # --- Location API Methods ---

    def get_location_categories_api(self):
        """API endpoint to get location categories."""
        logging.info("API: get_location_categories_api called.")
        result = app_logic.get_location_categories_logic() # Delegate
        logging.info(f"API: get_location_categories_api returning {len(result.get('categories',{}))} categories.")
        return result

    def get_locations_in_category_api(self, category_filename):
        """API endpoint to get locations within a specific category file."""
        logging.info(f"API: get_locations_in_category_api called for file: '{category_filename}'")
        result = app_logic.get_locations_in_category_logic(category_filename) # Delegate
        logging.info(f"API: get_locations_in_category_api returning {len(result.get('locations',{}))} locations.")
        return result

    def teleport_to_location_api(self, location_id):
        """API endpoint to teleport the player to a location ID."""
        logging.info(f"API: teleport_to_location_api called for ID: '{location_id}'")
        result = app_logic.teleport_to_location_logic(location_id) # Delegate
        logging.info(f"API: teleport_to_location_api result: {result}")
        return result

# --- Main Execution Logic --- 
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="ES4R Companion - GUI or CLI")
    parser.add_argument("--cli", action="store_true", help="Run in Command Line Interface mode.")
    args = parser.parse_args()

    api_instance = Api() 

    if args.cli:
        # Run the CLI version (defined in cli_ui.py)
        print("Starting CLI mode...")
        run_companion_cli(automator)
    else:
        # Start the pywebview GUI
        print("Starting GUI mode...")
        try:
            # Create the pywebview window
            window = webview.create_window(
                'ES4R Companion',
                'gui/index.html',
                js_api=api_instance, 
                width=1000, 
                height=1071,
                resizable=True
            )

            # --- Threading Setup --- Removed section
            # status_thread = threading.Thread(...)
            # status_thread.start()

            # --- Graceful Shutdown --- Removed section
            # def on_closed():
            #    ...
            # window.events.closed += on_closed

            # Start the event loop
            webview.start(debug=False) # Keep debug=False for release maybe
        except Exception as e:
            logging.exception("Failed to start GUI")
            print(f"FATAL: Failed to start GUI: {e}")
            print("Ensure you have a compatible WebView2 runtime installed.")
            exit(1) 