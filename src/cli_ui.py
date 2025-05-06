"""
Handles the Command Line Interface (CLI) user interactions and flow.
"""
import sys
import os
import time
import colorama
from colorama import Fore, Back, Style
import logging

# Ensure correct import path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import necessary components from main application/logic
import app # To access automator/game_found status
from src import app_logic # Import the logic layer
from src.command_builder import build_additem_command
from src.data_loader import get_item_categories, load_json_data
from src.automator import WindowAutomator # Import for type hinting

# --- CLI UI Constants & Helpers ---
COLOR_MENU = Fore.CYAN
COLOR_PROMPT = Fore.YELLOW
COLOR_INFO = Fore.GREEN
COLOR_WARN = Fore.MAGENTA
COLOR_ERROR = Fore.RED
COLOR_RESET = Style.RESET_ALL

COMMAND_HISTORY = [] # Simple in-memory history for the session

# Global automator instance for the CLI session
cli_automator: WindowAutomator = None

def print_header(title):
    print(f"\n{COLOR_MENU}{'=' * 10} {title} {'=' * 10}{COLOR_RESET}")

def print_menu(options):
    for key, value in options.items():
        print(f"  {COLOR_MENU}{key}{COLOR_RESET}: {value}")
    print(f"  {COLOR_MENU}q{COLOR_RESET}: Quit")

def get_choice(prompt="Enter choice: "):
    return input(f"{COLOR_PROMPT}{prompt}{COLOR_RESET}").strip().lower()

def print_status():
    global cli_automator
    if not cli_automator:
        print(f"{COLOR_ERROR}Error: Automator not initialized for CLI.{COLOR_RESET}")
        return False
    # Use the logic layer function which now handles debug mode
    status_result = app_logic.check_game_status_logic() # This uses app.automator, ensure consistency?
    # Let's use the passed cli_automator instance instead for consistency
    status_msg = ""
    if cli_automator.is_in_debug_mode():
        debug_file = os.path.basename(cli_automator.get_debug_filepath() or "debug.txt")
        status_msg = f"Debug Mode Active ({debug_file})"
    elif cli_automator.hwnd:
        status_msg = "Game Found"
    else:
        status_msg = "Game Not Found"

    status_color = COLOR_INFO if "Found" in status_msg else \
                   (COLOR_WARN if "Debug" in status_msg else COLOR_ERROR)

    print(f"\n{status_color}Game Status: {status_msg}{COLOR_RESET}")
    # Return True if game is found OR if in debug mode (as commands can be logged)
    return cli_automator.hwnd is not None or cli_automator.is_in_debug_mode()

def confirm_action(prompt="Are you sure?"):
    choice = input(f"{COLOR_WARN}{prompt} (y/N): {COLOR_RESET}").strip().lower()
    return choice == 'y'

# --- Core Action Functions (CLI versions) ---

def cli_run_single_command():
    print_header("Run Single Command")
    if not print_status():
        print(f"{COLOR_ERROR}Cannot run command, game not found.{COLOR_RESET}")
        return

    command = input(f"{COLOR_PROMPT}Enter command (or 'h' for history): {COLOR_RESET}").strip()
    if command == 'h':
        if not COMMAND_HISTORY:
            print(f"{COLOR_INFO}Command history is empty.{COLOR_RESET}")
            return
        print("--- Command History ---")
        for i, cmd in enumerate(reversed(COMMAND_HISTORY)): # Show most recent first
            print(f"  {i+1}: {cmd}")
        try:
            choice = int(input(f"{COLOR_PROMPT}Enter history number to run: {COLOR_RESET}"))
            if 1 <= choice <= len(COMMAND_HISTORY):
                command = COMMAND_HISTORY[-choice] # Get command from reversed index
                print(f"{COLOR_INFO}Selected from history: {command}{COLOR_RESET}")
            else:
                print(f"{COLOR_ERROR}Invalid history number.{COLOR_RESET}")
                return
        except ValueError:
            print(f"{COLOR_ERROR}Invalid input.{COLOR_RESET}")
            return
            
    if not command:
        print(f"{COLOR_WARN}Command cannot be empty.{COLOR_RESET}")
        return

    print(f"{COLOR_INFO}Executing: {command}...{COLOR_RESET}")
    COMMAND_HISTORY.append(command)
    result = app_logic.run_single_command_logic(command)
    if result["success"]:
        print(f"{COLOR_INFO}Command executed successfully.{COLOR_RESET}")
        # Ask to save favorite
        if confirm_action("Save this command as a favorite?"):
            fav_name = input(f"{COLOR_PROMPT}Enter a name for this favorite: {COLOR_RESET}").strip()
            save_result = app_logic.save_favorite_logic(fav_name, command, 'single')
            if save_result['status'] == 'success':
                print(f"{COLOR_INFO}{save_result['message']}{COLOR_RESET}")
            else:
                print(f"{COLOR_ERROR}{save_result['message']}{COLOR_RESET}")
                
    else:
        print(f"{COLOR_ERROR}Command failed: {result.get('message', 'Unknown error')}{COLOR_RESET}")

def cli_run_preset_battle():
    print_header("Run Preset Battle")
    if not print_status():
        print(f"{COLOR_ERROR}Cannot run preset, game not found.{COLOR_RESET}")
        return
        
    presets_result = app_logic.get_presets_logic("battle")
    presets = presets_result.get('presets', [])
    if not presets:
        print(f"{COLOR_WARN}No battle presets found.{COLOR_RESET}")
        return
        
    print("Available Presets:")
    for i, name in enumerate(presets):
        print(f"  {i+1}: {name}")
        
    try:
        choice_idx = int(get_choice("Select preset number: ")) - 1
        if 0 <= choice_idx < len(presets):
            preset_name = presets[choice_idx]
            print(f"{COLOR_INFO}Running preset: {preset_name}...{COLOR_RESET}")
            result = app_logic.run_preset_logic(preset_name, "battle")
            if result["success"]:
                print(f"{COLOR_INFO}Preset '{preset_name}' completed successfully.{COLOR_RESET}")
            else:
                print(f"{COLOR_ERROR}Preset '{preset_name}' failed: {result.get('message', 'Execution error')}{COLOR_RESET}")
        else:
            print(f"{COLOR_ERROR}Invalid preset number.{COLOR_RESET}")
    except ValueError:
        print(f"{COLOR_ERROR}Invalid input.{COLOR_RESET}")

def cli_add_item():
    print_header("Add Item")
    if not print_status():
        print(f"{COLOR_ERROR}Cannot add item, game not found.{COLOR_RESET}")
        return

    # 1. Select Category
    categories_result = app_logic.get_item_categories_logic()
    categories = categories_result.get("categories", {})
    if not categories:
         print(f"{COLOR_WARN}No item categories found.{COLOR_RESET}")
         return
    category_list = list(categories.items()) # List of (name, filename)
    print("Item Categories:")
    for i, (name, _) in enumerate(category_list):
        print(f"  {i+1}: {name}")
    try:
        cat_choice_idx = int(get_choice("Select category number: ")) - 1
        if not (0 <= cat_choice_idx < len(category_list)):
            print(f"{COLOR_ERROR}Invalid category number.{COLOR_RESET}")
            return
        cat_name, cat_filename = category_list[cat_choice_idx]
        print(f"{COLOR_INFO}Selected category: {cat_name}{COLOR_RESET}")
    except ValueError:
        print(f"{COLOR_ERROR}Invalid input.{COLOR_RESET}")
        return

    # 2. Select Item
    items_result = app_logic.get_items_in_category_logic(cat_filename)
    items = items_result.get("items", {})
    if not items:
         print(f"{COLOR_WARN}No items found in category '{cat_name}'.{COLOR_RESET}")
         return
    item_list = list(items.items()) # List of (name, id)
    print(f"Items in {cat_name}:")
    # Simple pagination or scrolling if list is long?
    # For now, just list all. Might be too long.
    # TODO: Add pagination if list exceeds ~20 items
    for i, (name, item_id) in enumerate(item_list):
        print(f"  {i+1}: {name} ({item_id})")
    try:
        item_choice_idx = int(get_choice("Select item number: ")) - 1
        if not (0 <= item_choice_idx < len(item_list)):
            print(f"{COLOR_ERROR}Invalid item number.{COLOR_RESET}")
            return
        item_name, item_id = item_list[item_choice_idx]
        print(f"{COLOR_INFO}Selected item: {item_name} ({item_id}){COLOR_RESET}")
    except ValueError:
        print(f"{COLOR_ERROR}Invalid input.{COLOR_RESET}")
        return
        
    # 3. Enter Quantity
    try:
        quantity = int(get_choice("Enter quantity: "))
        if quantity <= 0:
            print(f"{COLOR_ERROR}Quantity must be positive.{COLOR_RESET}")
            return
    except ValueError:
        print(f"{COLOR_ERROR}Invalid quantity.{COLOR_RESET}")
        return
        
    # 4. Execute
    print(f"{COLOR_INFO}Adding {quantity} x {item_name}...{COLOR_RESET}")
    result = app_logic.add_item_logic(item_id, quantity)
    if result["success"]:
        print(f"{COLOR_INFO}Item(s) added successfully.{COLOR_RESET}")
        # Ask to save favorite
        if confirm_action("Save this additem command as a favorite?"):
            # Suggest a default name
            default_fav_name = f"Add {quantity} {item_name}"
            fav_name = input(f"{COLOR_PROMPT}Enter name for favorite (default: '{default_fav_name}'): {COLOR_RESET}").strip()
            if not fav_name:
                fav_name = default_fav_name
                
            command_str = result.get('command') # Get command from result dict
            if command_str: 
                save_result = app_logic.save_favorite_logic(fav_name, command_str, 'additem')
                if save_result['status'] == 'success':
                    print(f"{COLOR_INFO}{save_result['message']}{COLOR_RESET}")
                else:
                    print(f"{COLOR_ERROR}{save_result['message']}{COLOR_RESET}")
            else:
                 print(f"{COLOR_ERROR}Could not retrieve command string to save favorite.{COLOR_RESET}")
                 
    else:
        print(f"{COLOR_ERROR}Failed to add item: {result.get('message', 'Unknown error')}{COLOR_RESET}")

# --- Favorites Management (CLI) ---

def cli_list_favorites():
    print_header("List Favorites")
    fav_result = app_logic.load_favorites_logic()
    favorites = fav_result.get('favorites', [])
    if not favorites:
        print(f"{COLOR_INFO}You have no saved favorites.{COLOR_RESET}")
        return
        
    print(f"{COLOR_INFO}Saved Favorites ({len(favorites)}):{COLOR_RESET}")
    # Sort by name for display
    favorites.sort(key=lambda x: x.get('name', ''))
    for i, fav in enumerate(favorites):
        name = fav.get('name', 'Unnamed')
        cmd = fav.get('command', 'No Command')
        typ = fav.get('type', 'unknown')
        print(f"  {COLOR_MENU}{i+1}{COLOR_RESET}: {name} ({typ}) - `{cmd}`")
        
def cli_run_favorite():
    print_header("Run Favorite")
    if not print_status():
        print(f"{COLOR_ERROR}Cannot run favorite, game not found.{COLOR_RESET}")
        return
        
    fav_result = app_logic.load_favorites_logic()
    favorites = fav_result.get('favorites', [])
    if not favorites:
        print(f"{COLOR_INFO}You have no saved favorites to run.{COLOR_RESET}")
        return
        
    print("Select Favorite to Run:")
    favorites.sort(key=lambda x: x.get('name', ''))
    for i, fav in enumerate(favorites):
         print(f"  {COLOR_MENU}{i+1}{COLOR_RESET}: {fav.get('name', 'Unnamed')}")
         
    try:
        choice_idx = int(get_choice("Select favorite number: ")) - 1
        if 0 <= choice_idx < len(favorites):
            fav_name = favorites[choice_idx].get('name')
            if not fav_name:
                 print(f"{COLOR_ERROR}Selected favorite has no name.{COLOR_RESET}")
                 return
                 
            print(f"{COLOR_INFO}Running favorite: {fav_name}...{COLOR_RESET}")
            result = app_logic.run_favorite_logic(fav_name)
            # Result message from logic layer already includes context
            msg_color = COLOR_INFO if result['success'] else COLOR_ERROR
            print(f"{msg_color}{result.get('message', 'Execution complete.')}{COLOR_RESET}")
        else:
            print(f"{COLOR_ERROR}Invalid favorite number.{COLOR_RESET}")
    except ValueError:
        print(f"{COLOR_ERROR}Invalid input.{COLOR_RESET}")
        
def cli_add_favorite():
    print_header("Add Favorite Manually")
    fav_name = input(f"{COLOR_PROMPT}Enter name for the new favorite: {COLOR_RESET}").strip()
    fav_command = input(f"{COLOR_PROMPT}Enter the command string: {COLOR_RESET}").strip()
    # For simplicity, mark manually added as 'single' type
    fav_type = 'single' 
    
    if not fav_name or not fav_command:
        print(f"{COLOR_ERROR}Favorite name and command cannot be empty.{COLOR_RESET}")
        return
        
    save_result = app_logic.save_favorite_logic(fav_name, fav_command, fav_type)
    msg_color = COLOR_INFO if save_result['status'] == 'success' else COLOR_ERROR
    print(f"{msg_color}{save_result['message']}{COLOR_RESET}")

def cli_delete_favorite():
    print_header("Delete Favorite")
    fav_result = app_logic.load_favorites_logic()
    favorites = fav_result.get('favorites', [])
    if not favorites:
        print(f"{COLOR_INFO}You have no saved favorites to delete.{COLOR_RESET}")
        return
        
    print("Select Favorite to Delete:")
    favorites.sort(key=lambda x: x.get('name', ''))
    for i, fav in enumerate(favorites):
         print(f"  {COLOR_MENU}{i+1}{COLOR_RESET}: {fav.get('name', 'Unnamed')}")
         
    try:
        choice_idx = int(get_choice("Select favorite number: ")) - 1
        if 0 <= choice_idx < len(favorites):
            fav_name = favorites[choice_idx].get('name')
            if not fav_name:
                 print(f"{COLOR_ERROR}Selected favorite has no name.{COLOR_RESET}")
                 return

            if confirm_action(f"Delete favorite '{fav_name}'?"):         
                print(f"{COLOR_INFO}Deleting favorite: {fav_name}...{COLOR_RESET}")
                result = app_logic.delete_favorite_logic(fav_name)
                msg_color = COLOR_INFO if result['success'] else COLOR_ERROR
                print(f"{msg_color}{result.get('message', 'Deletion attempt finished.')}{COLOR_RESET}")
            else:
                print(f"{COLOR_INFO}Deletion cancelled.{COLOR_RESET}")
        else:
            print(f"{COLOR_ERROR}Invalid favorite number.{COLOR_RESET}")
    except ValueError:
        print(f"{COLOR_ERROR}Invalid input.{COLOR_RESET}")

def cli_manage_favorites():
    """Handles the favorites sub-menu."""
    while True:
        print_header("Manage Favorites")
        menu_options = {
            'l': 'List Favorites',
            'r': 'Run Favorite',
            'a': 'Add Favorite Manually',
            'd': 'Delete Favorite'
        }
        print_menu(menu_options)
        choice = get_choice("Favorites menu choice: ")
        
        if choice == 'l':
            cli_list_favorites()
        elif choice == 'r':
            cli_run_favorite()
        elif choice == 'a':
            cli_add_favorite()
        elif choice == 'd':
            cli_delete_favorite()
        elif choice == 'q':
            break
        else:
            print(f"{COLOR_ERROR}Invalid choice.{COLOR_RESET}")
        input(f"\n{COLOR_INFO}Press Enter to return to Favorites Menu...{COLOR_RESET}")

# --- Main CLI Loop ---

def run_companion_cli(automator_instance: WindowAutomator):
    """Runs the main command-line interface loop."""
    global cli_automator
    cli_automator = automator_instance # Store the passed instance globally for this module

    print("=" * 30)
    print(" ES4R Companion CLI ")
    print("=" * 30)
    print("Type 'help' for commands, 'exit' to quit.")

    # Initial status check
    print_status()

    while True:
        try:
            user_input = input("> ")
            if not handle_input(user_input):
                break
        except EOFError:
            print("\nExiting...")
            break
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"{COLOR_ERROR}\nAn unexpected error occurred: {e}{COLOR_RESET}")
            logging.exception("Unexpected CLI error")

def handle_input(user_input):
    """Processes user input from the CLI."""
    global cli_automator # Needed to potentially re-check status
    parts = user_input.lower().split()
    if not parts:
        return True # Continue loop

    command = parts[0]

    if command in ['exit', 'quit']:
        print("Exiting ES4R Companion CLI.")
        return False # Stop loop
    elif command == 'help':
        print_help()
    elif command == 'status':
        # Re-run the check and print
        if cli_automator: # Check if automator exists
             print("Re-checking game status...")
             cli_automator.find_process_and_window() # Perform a fresh check
        print_status()
    elif command == 'exec':
        if len(parts) > 1:
            full_command = user_input[len("exec "):].strip()
            execute_cli_command(full_command)
        else:
            print(f"{COLOR_WARN}Usage: exec <full console command>{COLOR_RESET}")
    elif command == 'additem':
        # Simplified: expects 'additem <item_id> <quantity>'
        if len(parts) == 3:
            item_id = parts[1]
            try:
                quantity = int(parts[2])
                # TODO: Validate item_id format?
                built_command = app_logic.build_additem_command_logic(item_id, quantity)
                if built_command['success']:
                     execute_cli_command(built_command['command'])
                else:
                     print(f"{COLOR_ERROR}Error building command: {built_command['message']}{COLOR_RESET}")
            except ValueError:
                print(f"{COLOR_WARN}Invalid quantity: '{parts[2]}'. Must be a number.{COLOR_RESET}")
        else:
            print(f"{COLOR_WARN}Usage: additem <item_id> <quantity>{COLOR_RESET}")
    # Add other specific commands (placeatme, presets, etc.) here as needed
    # elif command == 'placeatme': ...
    # elif command == 'preset': ...
    else:
        print(f"{COLOR_WARN}Unknown command: '{command}'. Type 'help' for options.{COLOR_RESET}")

    return True # Continue loop

def execute_cli_command(command_str):
    global cli_automator
    if not cli_automator:
        print(f"{COLOR_ERROR}Error: Automator not initialized.{COLOR_RESET}")
        return
    if not command_str:
        print(f"{COLOR_WARN}Please enter a command.{COLOR_RESET}")
        return

    print(f"{COLOR_INFO}Executing: {command_str}...{COLOR_RESET}")
    # Use the passed automator instance directly
    success = cli_automator.execute_command(command_str, verbose=True) # Use verbose for CLI

    if success:
        if cli_automator.is_in_debug_mode():
             print(f"{COLOR_WARN}Success: Command logged to debug file.{COLOR_RESET}")
        else:
            print(f"{COLOR_SUCCESS}Success: Command executed in game.{COLOR_RESET}")
    else:
        # Automator execute_command handles internal logging of errors
        if cli_automator.is_in_debug_mode():
            # Failure in debug mode usually means setup failed
            print(f"{COLOR_ERROR}Error: Failed to log command to debug file. Check logs.{COLOR_RESET}")
        else:
            print(f"{COLOR_ERROR}Error: Command execution failed. Check game console or logs.{COLOR_RESET}")

if __name__ == '__main__':
    # This allows running the CLI directly for testing if needed
    # Assumes the automator and other setup happens when app module is imported
    run_companion_cli()