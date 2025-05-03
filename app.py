import webview
import argparse
import threading
import time
import sys
import os
import platform
import win32gui
import win32api
import win32console
import logging
import traceback
import colorama
from colorama import Fore, Back, Style

# Ensure src is importable (adjust path if necessary)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.automator import WindowAutomator
from src.data_loader import load_json_data, get_item_categories
from src.command_builder import build_additem_command
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

# --- Logging Setup (Moved from main.py) ---
try:
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s',
        filename=log_file,
        filemode='w'
    )
    logging.info("--- Application Starting ---")
except Exception as log_setup_e:
    print(f"FATAL: Could not set up logging: {log_setup_e}")
    # Simple print error if logging fails, GUI won't have Tkinter fallback
    exit(1)

# --- API Class for pywebview --- 
class Api:
    def __init__(self):
        # Maybe run initial check in background?
        self._check_game_thread = threading.Thread(target=self._initial_game_check, daemon=True)
        self._check_game_thread.start()
        
    def _initial_game_check(self):
        global game_found, automator
        print("API/CLI: Performing initial game check...")
        game_found = automator.find_process_and_window()
        print(f"API/CLI: Initial game check complete. Found: {game_found}")

    def check_status(self):
        """Checks if the game process/window is found."""
        global game_found
        # Optionally re-check or just return cached status
        # Re-checking could be slow, let's return cached for now
        # game_found = automator.find_process_and_window() 
        status_msg = "Game Found" if game_found else "Game Not Found"
        print(f"API: check_status called, returning: {status_msg}")
        return {"status": status_msg}

    def run_single_command(self, command):
        """Executes a single command via the automator."""
        global game_found
        print(f"API: Received single command: {command}")
        if not game_found:
            print("API: Game not found, cannot run command.")
            return {"success": False, "message": "Game not found"}
        if not command or not isinstance(command, str):
             print("API: Invalid command received.")
             return {"success": False, "message": "Invalid command"}
             
        # Run the full cycle (open, exec, close) - non-verbose from GUI
        success = automator.execute_command(command.strip(), verbose=False)
        print(f"API: Single command execution result: {success}")
        # Try to refocus GUI window? Requires window object passed to Api or global.
        return {"success": success}

    def get_battle_presets(self):
        """Loads and returns the list of battle preset names."""
        print("API: Getting battle presets...")
        preset_data = load_json_data("battles.json")
        if preset_data and isinstance(preset_data, dict):
            presets = list(preset_data.keys())
            print(f"API: Found presets: {presets}")
            return {"presets": presets}
        else:
            print("API: No presets found or error loading.")
            return {"presets": []}

    def run_preset_battle(self, preset_name):
        """Runs a sequence of commands from a named battle preset."""
        global game_found
        print(f"API: Received run preset request: {preset_name}")
        if not game_found:
             print("API: Game not found, cannot run preset.")
             return {"success": False, "message": "Game not found"}
        if not preset_name:
             print("API: Invalid preset name.")
             return {"success": False, "message": "Invalid preset name"}

        preset_data = load_json_data("battles.json")
        if not preset_data or preset_name not in preset_data:
            print(f"API: Preset '{preset_name}' not found in data.")
            return {"success": False, "message": f"Preset '{preset_name}' not found"}

        commands = preset_data[preset_name]
        if not commands or not isinstance(commands, list):
             print(f"API: Invalid command list found for preset '{preset_name}'.")
             return {"success": False, "message": f"Invalid commands for '{preset_name}'"}

        print(f"API: Executing preset '{preset_name}' with {len(commands)} commands...")
        # Execute using the open/exec/close sequence
        all_succeeded = False
        if automator.open_console(verbose=False): # Non-verbose from GUI
            all_succeeded = True
            for cmd in commands:
                success = automator.execute_command_in_console(cmd, verbose=False)
                if not success:
                    print(f"API: Command '{cmd}' failed in preset '{preset_name}'. Stopping.")
                    all_succeeded = False
                    break
                time.sleep(0.5) # Keep delay between commands
            automator.close_console(verbose=False)
        else:
            print("API: Failed to open console for preset execution.")
            all_succeeded = False
            
        print(f"API: Preset execution finished. Success: {all_succeeded}")
        return {"success": all_succeeded}

    # --- Item API Methods ---
    def get_item_categories_api(self):
        """Loads and returns item category names and filenames."""
        print("API: Getting item categories...")
        categories = get_item_categories() # Returns dict {name: filename}
        if categories:
            print(f"API: Found categories: {list(categories.keys())}")
            return {"categories": categories}
        else:
            print("API: No item categories found.")
            return {"categories": {}}

    def get_items_in_category(self, filename):
        """Loads items from a specific category file."""
        print(f"API: Getting items for category file: {filename}")
        if not filename or '..' in filename or filename.startswith('/') or filename.startswith('\\'):
            print("API: Invalid or potentially unsafe filename rejected.")
            return {"items": {}} # Return empty dict for invalid filename
            
        item_data = load_json_data(filename) # Returns dict {name: id} or None
        if item_data and isinstance(item_data, dict):
            # Sort items by name for consistent display
            sorted_items = dict(sorted(item_data.items()))
            print(f"API: Found {len(sorted_items)} items.")
            return {"items": sorted_items}
        else:
            print(f"API: No items found or error loading '{filename}'.")
            return {"items": {}}

    def add_item(self, item_id, quantity):
        """Builds and executes the additem command."""
        global game_found, automator
        print(f"API: Received add item request: ID={item_id}, Qty={quantity}")
        if not game_found:
            print("API: Game not found, cannot add item.")
            return {"success": False, "message": "Game not found"}
        
        try:
            # Validate quantity server-side as well
            qty = int(quantity)
            if qty <= 0:
                raise ValueError("Quantity must be positive")
        except (ValueError, TypeError):
            print(f"API: Invalid quantity received: {quantity}")
            return {"success": False, "message": "Invalid quantity"}
        if not item_id or not isinstance(item_id, str):
            print(f"API: Invalid item ID received: {item_id}")
            return {"success": False, "message": "Invalid item ID"}

        command_string = build_additem_command(item_id, qty)
        print(f"API: Built command: {command_string}")
        
        # Use single command execution (open/exec/close)
        success = automator.execute_command(command_string, verbose=False)
        print(f"API: Add item execution result: {success}")
        return {"success": success}

# --- Main Execution Logic --- 
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="ES4 Companion - GUI or CLI")
    parser.add_argument("--cli", action="store_true", help="Run in Command Line Interface mode.")
    args = parser.parse_args()

    # Create Api instance to trigger initial game check (background thread)
    api_instance = Api() 
    # Small delay to allow the background check thread to start and potentially find the game
    # especially important for CLI mode which checks status almost immediately.
    time.sleep(0.5) 

    if args.cli:
        print("Starting CLI Mode...")
        try:
            # Call the imported CLI main function
            run_companion_cli() 
            logging.info("CLI mode finished.")
        except Exception as e:
            logging.error("An unhandled exception occurred in CLI mode:", exc_info=True)
            print(f"\nCRITICAL ERROR: {e}\nSee {log_file} for details.")
        finally:
            logging.info("--- Application Exiting (CLI) ---")
            print(Style.RESET_ALL)
    else:
        print("Starting GUI Mode...")
        # api_instance is already created
        window = webview.create_window(
            'ES4 Companion',
            'gui/index.html',
            js_api=api_instance,
            width=600, 
            height=500
        )
        # Pass debug=True to potentially see web inspector errors
        webview.start(debug=True) 
        print("GUI window closed.")
        logging.info("--- Application Exiting (GUI) ---") 