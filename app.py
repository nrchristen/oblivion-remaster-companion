import webview
import argparse
import threading
import time
import sys
import os
import platform
import logging
import traceback
import colorama
from colorama import Fore, Back, Style

# Ensure src is importable (adjust path if necessary)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.automator import WindowAutomator
from src.data_loader import load_json_data, get_item_categories
from src.command_builder import build_additem_command, build_placeatme_command
# Import the new logic layer
from src import app_logic 
# Import the new CLI entry point
from src.cli_ui import run_companion_cli

# --- Global Variables (Careful with state if making multi-threaded later) ---
TARGET_EXECUTABLE = "OblivionRemastered-WinGDK-Shipping.exe" # Or load from config
automator = WindowAutomator(TARGET_EXECUTABLE)
game_found = False
log_file = 'companion_log.txt'

# Colorama Setup
COLOR_TEXT = Fore.YELLOW
COLOR_BG = Back.RED
COLOR_INDICATOR = Fore.LIGHTRED_EX
COLOR_RESET = Style.RESET_ALL
colorama.init(autoreset=True)

# --- Logging Setup (Explicit Configuration) ---
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s:%(lineno)d - %(message)s')
logger = logging.getLogger() # Get the root logger
logger.setLevel(logging.DEBUG) # Set the lowest level for the logger

# Clear existing handlers (important if this runs multiple times or other libs configure logging)
if logger.hasHandlers():
    logger.handlers.clear()

# File Handler (always log DEBUG level to file)
try:
    file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(log_formatter)
    logger.addHandler(file_handler)
    logging.info("--- File logging configured ---") # Use logging directly now
except Exception as log_setup_e:
    # If file logging fails, we can't log to file, print critical error
    print(f"FATAL: Could not set up file logging to {log_file}: {log_setup_e}")
    exit(1)

# Optional: Console Handler (show INFO level to console when running)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO) # Show INFO and above in console
console_handler.setFormatter(log_formatter)
logger.addHandler(console_handler)
logging.info("--- Console logging configured ---")

# --- API Class for pywebview --- 
class Api:
    def __init__(self):
        # Maybe run initial check in background?
        self._check_game_thread = threading.Thread(target=self._initial_game_check, daemon=True)
        self._check_game_thread.start()
        
    def _initial_game_check(self):
        global game_found, automator
        logging.info("Starting initial game check (background thread)...")
        game_found = automator.find_process_and_window() # Uses enhanced automator
        logging.info(f"Initial game check complete. Found: {game_found}")

    def check_status(self):
        """Checks if the game process/window is found."""
        global game_found # Still uses the cached global here, for speed
        logging.info("API: check_status called.")
        # Optionally re-check or just return cached status
        # Re-checking could be slow, let's return cached for now
        # game_found = automator.find_process_and_window() 
        status_msg = "Game Found" if game_found else "Game Not Found"
        logging.info(f"API: check_status returning cached status: {status_msg}")
        return {"status": status_msg}

    def run_single_command(self, command):
        """Executes a single command via the automator."""
        logging.info(f"API: run_single_command called with command: \"{command}\"")
        # Delegate validation and execution to logic layer
        result = app_logic.run_single_command_logic(command)
        logging.info(f"API: run_single_command result: {result}")
        return result

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

# --- Main Execution Logic --- 
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="ES4R Companion - GUI or CLI")
    parser.add_argument("--cli", action="store_true", help="Run in Command Line Interface mode.")
    args = parser.parse_args()

    # Create Api instance to trigger initial game check (background thread)
    api_instance = Api() 
    # Small delay to allow the background check thread to start and potentially find the game
    # especially important for CLI mode which checks status almost immediately.
    time.sleep(0.5) 

    if args.cli:
        # Run the CLI version (defined in cli_ui.py)
        print("Starting CLI mode...")
        run_companion_cli()
    else:
        # Start the pywebview GUI
        print("Starting GUI mode...")
        try:
            webview.create_window(
                'ES4R Companion',
                'gui/index.html',
                js_api=api_instance, 
                width=900, 
                height=1071,
                resizable=True # Allow resizing
            )
            webview.start(debug=True) # Enable debug for console messages
        except Exception as e:
            logging.exception("Failed to start GUI")
            print(f"FATAL: Failed to start GUI: {e}")
            print("Ensure you have a compatible WebView2 runtime installed.")
            exit(1) 