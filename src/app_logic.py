"""
Core application logic/service layer, independent of UI (GUI or CLI).
Handles interaction with automator, data loader, and command builder.
"""
import time
import logging
import os

# Need to access the shared automator instance and game_found status.
# How to handle this? Pass them in? Use globals from app.py?
# Using globals is simpler for this structure but less SOLID.
# Let's import app and access its globals for now.
# A better approach would be dependency injection if complexity grew.
import app 

from src import data_loader
from src import command_builder
from src.data_loader import load_json_data, get_item_categories, add_battle_preset, save_json_data, FAVORITES_FILE
from src.command_builder import build_additem_command, build_placeatme_command, build_teleport_command

def check_game_status_logic():
    """Checks the current game status, including debug mode."""
    logging.debug("Entering check_game_status_logic")
    # Access global automator instance from app.py
    automator = app.automator
    
    # Actively try to find the window *before* checking status
    automator.find_process_and_window()

    if automator.is_in_debug_mode():
        debug_file = os.path.basename(automator.get_debug_filepath() or "debug.txt")
        status_msg = f"Debug Mode Active ({debug_file})"
        logging.info(f"Checked game status: {status_msg}")
    elif automator.hwnd:
        status_msg = "Game Found"
        logging.info(f"Checked game status: {status_msg} (HWND: {automator.hwnd})")
    else:
        # This case might happen briefly during startup or if find fails unexpectedly
        # without entering debug mode (though find_process_and_window tries to always enter debug on fail)
        status_msg = "Game Not Found"
        logging.warning("Checked game status: Game Not Found (and not in debug mode)")

    return {"status": status_msg}

def run_single_command_logic(command):
    """Handles validation and execution for a single command string."""
    logging.debug(f"Entering run_single_command_logic with command: \"{command}\"")
    # Removed check for app.game_found - automator.execute_command handles it now,
    # including the debug mode logic.
    if not command or not isinstance(command, str):
         logging.warning(f"Invalid command received in logic: {command}")
         return {"success": False, "message": "Invalid command"}

    # Use the execute_command (full cycle) method from the shared automator
    # This method now performs its own find_process_and_window check.
    command_string = command.strip()
    logging.info(f"Attempting to execute single command: {command_string}")
    success = app.automator.execute_command(command_string, verbose=False) # GUI/API usually non-verbose
    logging.info(f"Single command execution result: {success}")
    result = {"success": success}
    if not success:
        # Provide a more specific message depending on mode
        automator = app.automator # Get automator instance
        if automator.is_in_debug_mode():
            result['message'] = f"Command logged to debug file. Game not found."
        else:
            result['message'] = f"Failed to execute command. Check log or ensure game is focused."
    logging.debug(f"Exiting run_single_command_logic, result: {result}")
    return result

def get_presets_logic(preset_type="battle"):
    """Loads presets of a given type (e.g., 'battle')."""
    logging.debug(f"Entering get_presets_logic for type: {preset_type}")
    filename = f"{preset_type}s.json" # Assumes plural naming convention
    print(f"LOGIC: Getting presets from {filename}...")
    preset_data = load_json_data(filename)
    if preset_data and isinstance(preset_data, dict):
        presets = list(preset_data.keys())
        print(f"LOGIC: Found presets: {presets}")
        logging.debug(f"Exiting get_presets_logic, found {len(presets)} presets.")
        return {"presets": presets}
    else:
        print(f"LOGIC: No presets found or error loading {filename}.")
        logging.debug(f"Exiting get_presets_logic, found 0 presets.")
        return {"presets": []}

def run_command_sequence_logic(commands, sequence_name="sequence"):
     """Opens console, runs a list of commands, closes console."""
     logging.debug(f"Entering run_command_sequence_logic: sequence='{sequence_name}', commands={len(commands)}")
     # Removed app.game_found check - automator.open_console handles it now.
     # if not app.game_found:
     # ...
     if not commands or not isinstance(commands, list):
          logging.warning(f"Invalid command list for sequence '{sequence_name}'.")
          return {"success": False, "message": "Invalid command list"}

     all_succeeded = False
     # Use the shared automator instance
     # open_console now performs the check
     logging.info(f"Attempting to open console for sequence '{sequence_name}'")
     if app.automator.open_console(verbose=False): # Non-verbose from logic layer usually
         logging.info(f"Console opened successfully for sequence '{sequence_name}'")
         all_succeeded = True
         for i, cmd in enumerate(commands):
             logging.info(f"Executing {sequence_name} step {i+1}: {cmd}")
             success = app.automator.execute_command_in_console(cmd, verbose=False)
             if not success:
                 logging.error(f"Command '{cmd}' failed in {sequence_name}. Stopping sequence.")
                 all_succeeded = False
                 break
             time.sleep(0.5) # Keep delay between commands
         # Attempt to close console regardless of individual command success
         logging.info(f"Attempting to close console after sequence '{sequence_name}'")
         if not app.automator.close_console(verbose=False):
             logging.warning(f"Failed to close console cleanly after sequence '{sequence_name}'.")
             # Decide if this makes the whole sequence fail?
             # For now, let all_succeeded reflect command execution status.
     else:
         logging.error(f"Failed to open console for {sequence_name} execution.")
         all_succeeded = False
         
     logging.info(f"Sequence '{sequence_name}' execution finished. Overall success: {all_succeeded}")
     result = {"success": all_succeeded}
     if not all_succeeded:
         result['message'] = f"One or more commands failed during {sequence_name} execution."
     logging.debug(f"Exiting run_command_sequence_logic, result: {result}")
     return result

def run_preset_logic(preset_name, preset_type="battle"):
    """Loads a preset and runs its command sequence."""
    logging.debug(f"Entering run_preset_logic: name='{preset_name}', type='{preset_type}'")
    filename = f"{preset_type}s.json"
    print(f"LOGIC: Running preset '{preset_name}' from {filename}...")
    preset_data = load_json_data(filename)
    
    if not preset_data or preset_name not in preset_data:
        print(f"LOGIC: Preset '{preset_name}' not found in {filename}.")
        return {"success": False, "message": f"Preset '{preset_name}' not found"}

    commands = preset_data[preset_name]
    if not commands or not isinstance(commands, list):
         print(f"LOGIC: Invalid command list found for preset '{preset_name}'.")
         return {"success": False, "message": f"Invalid commands for '{preset_name}'"}
         
    # Delegate to the sequence execution logic
    logging.debug(f"Exiting run_preset_logic for '{preset_name}'")
    return run_command_sequence_logic(commands, sequence_name=f"preset '{preset_name}'")

def get_item_categories_logic():
    """Loads and returns item category names and filenames."""
    logging.debug("Entering get_item_categories_logic")
    print("LOGIC: Getting item categories...")
    categories = get_item_categories() # Returns dict {name: filename}
    if categories:
        print(f"LOGIC: Found categories: {list(categories.keys())}")
        logging.debug(f"Exiting get_item_categories_logic, found {len(categories)} categories.")
        return {"categories": categories}
    else:
        print("LOGIC: No item categories found.")
        logging.debug(f"Exiting get_item_categories_logic, found 0 categories.")
        return {"categories": {}}

def get_items_in_category_logic(filename):
    """Loads items from a specific category file."""
    logging.debug(f"Entering get_items_in_category_logic: filename='{filename}'")
    print(f"LOGIC: Getting items for category file: {filename}")
    if not filename or '..' in filename or filename.startswith('/') or filename.startswith('\\'):
        print("LOGIC: Invalid or potentially unsafe filename rejected.")
        return {"items": {}} # Return empty dict for invalid filename
        
    item_data = load_json_data(filename) # Returns dict {name: id} or None
    if item_data and isinstance(item_data, dict):
        sorted_items = dict(sorted(item_data.items()))
        print(f"LOGIC: Found {len(sorted_items)} items.")
        logging.debug(f"Exiting get_items_in_category_logic, found {len(sorted_items)} items.")
        return {"items": sorted_items}
    else:
        print(f"LOGIC: No items found or error loading '{filename}'.")
        logging.debug(f"Exiting get_items_in_category_logic, found 0 items.")
        return {"items": {}}

def add_item_logic(item_id, quantity):
    """Builds and executes the additem command."""
    logging.debug(f"Entering add_item_logic: ID={item_id}, Qty={quantity}")
    
    try:
        qty = int(quantity)
    except (ValueError, TypeError):
        logging.warning(f"Invalid quantity type received: {quantity}")
        return {"success": False, "message": "Invalid quantity"}

    # Check for non-positive quantity *after* successful conversion
    if qty <= 0:
        logging.warning(f"Non-positive quantity received: {quantity}")
        return {"success": False, "message": "Quantity must be positive"}
        
    if not item_id or not isinstance(item_id, str):
        logging.warning(f"Invalid item ID received: {item_id}")
        return {"success": False, "message": "Invalid item ID"}

    command_string = build_additem_command(item_id, qty)
    logging.info(f"Built additem command: {command_string}")
    
    # Delegate to single command logic (which uses execute_command full cycle)
    result = run_single_command_logic(command_string)
    result['command'] = command_string # Add command string to the result for favorite saving
    logging.debug(f"Exiting add_item_logic, result: {result}")
    return result

def get_npcs_logic():
    """Loads NPC data for selection."""
    filename = "npcs.json"
    print(f"LOGIC: Getting NPCs from {filename}...")
    npc_data = load_json_data(filename)
    if npc_data and isinstance(npc_data, dict):
        # Return dict {name: id} - GUI can sort if needed
        print(f"LOGIC: Found {len(npc_data)} NPCs.")
        return {"npcs": npc_data}
    else:
        print(f"LOGIC: No NPCs found or error loading {filename}.")
        return {"npcs": {}}

def save_battle_preset_logic(preset_name, command_list):
    """Handles the logic for saving a battle preset."""
    print(f"LOGIC: Attempting to save preset '{preset_name}'...")
    # add_battle_preset returns "success", "exists", or "error"
    status = add_battle_preset(preset_name, command_list)
    message = ""
    if status == "success":
        message = f"Preset '{preset_name}' saved successfully."
    elif status == "exists":
        message = f"Preset name '{preset_name}' already exists. Please choose another."
    else:
        message = f"Failed to save preset '{preset_name}'. See console/log for details."
    print(f"LOGIC: Save status: {status}, Message: {message}")
    return {"status": status, "message": message}

# --- Favorites Logic --- 

def load_favorites_logic():
    """Loads the list of favorites from the JSON file."""
    print(f"LOGIC: Loading favorites from {FAVORITES_FILE}...")
    favorites_data = load_json_data(FAVORITES_FILE)
    
    if favorites_data is None:
        # Error during load (logged by load_json_data)
        # Or file was just created as empty list, which is fine
        favorites_data = [] 
        
    if not isinstance(favorites_data, list):
        print(f"LOGIC: Favorites data is not a list. Resetting. Data: {favorites_data}")
        logging.warning(f"Favorites file ({FAVORITES_FILE}) was not a list. Resetting to empty list.")
        favorites_data = []
        # Optionally attempt to save the empty list back
        save_json_data(FAVORITES_FILE, favorites_data)

    # Ensure required keys exist? Maybe too strict. Assume correct structure for now.
    print(f"LOGIC: Found {len(favorites_data)} favorites.")
    return {"success": True, "favorites": favorites_data} # Always return a list

def save_favorite_logic(name, command, command_type):
    """Adds a new favorite command to the list.

    Args:
        name (str): The user-defined name for the favorite.
        command (str): The command string to save.
        command_type (str): Type of command ('additem', 'single', etc.).

    Returns:
        dict: { "status": "success"|"exists"|"error", "message": str }
    """
    print(f"LOGIC: Saving favorite: Name='{name}', Type='{command_type}'")
    if not name or not isinstance(name, str) or not name.strip():
        return {"status": "error", "message": "Favorite name cannot be empty."}
    if not command or not isinstance(command, str):
        return {"status": "error", "message": "Invalid command string."}
    if not command_type or not isinstance(command_type, str):
        # Default type if needed, or enforce?
        return {"status": "error", "message": "Invalid command type."}
        
    name = name.strip() # Clean whitespace
    command = command.strip()

    load_result = load_favorites_logic()
    # load_favorites_logic should always return success: True and a list now
    favorites = load_result['favorites']
    
    # Check for existing name (case-insensitive check? Let's do exact for now)
    if any(fav['name'] == name for fav in favorites if isinstance(fav, dict) and 'name' in fav):
        message = f"A favorite with the name '{name}' already exists." 
        print(f"LOGIC: {message}")
        return {"status": "exists", "message": message}

    new_favorite = {
        "name": name,
        "command": command,
        "type": command_type
    }
    favorites.append(new_favorite)

    if save_json_data(FAVORITES_FILE, favorites):
        message = f"Favorite '{name}' saved successfully."
        print(f"LOGIC: {message}")
        return {"status": "success", "message": message}
    else:
        message = f"Failed to save favorite '{name}' to file." # Error logged by save_json_data
        print(f"LOGIC: {message}")
        # Attempt to revert in-memory list? Maybe not necessary.
        return {"status": "error", "message": message}

def delete_favorite_logic(name):
    """Deletes a favorite by its name."""
    print(f"LOGIC: Deleting favorite: '{name}'...")
    if not name:
        return {"success": False, "message": "No favorite name provided."}
        
    load_result = load_favorites_logic()
    favorites = load_result['favorites']
    
    initial_length = len(favorites)
    # Filter out the favorite(s) with the matching name
    updated_favorites = [fav for fav in favorites if not (isinstance(fav, dict) and fav.get('name') == name)]
    
    if len(updated_favorites) == initial_length:
        message = f"Favorite '{name}' not found."
        print(f"LOGIC: {message}")
        return {"success": False, "message": message}
        
    if save_json_data(FAVORITES_FILE, updated_favorites):
        message = f"Favorite '{name}' deleted successfully."
        print(f"LOGIC: {message}")
        return {"success": True, "message": message}
    else:
        message = f"Failed to save favorites file after deleting '{name}'."
        print(f"LOGIC: {message}")
        return {"success": False, "message": message}

def run_favorite_logic(name):
    """Finds a favorite by name and executes its command."""
    logging.debug(f"Entering run_favorite_logic: name='{name}'")
    print(f"LOGIC: Running favorite: '{name}'...")
    if not name:
        return {"success": False, "message": "No favorite name provided."}
        
    load_result = load_favorites_logic()
    favorites = load_result['favorites']
    
    found_fav = None
    for fav in favorites:
        if isinstance(fav, dict) and fav.get('name') == name:
            found_fav = fav
            break
            
    if not found_fav:
        message = f"Favorite '{name}' not found."
        print(f"LOGIC: {message}")
        return {"success": False, "message": message}
        
    command_to_run = found_fav.get('command')
    if not command_to_run:
         message = f"Favorite '{name}' has an invalid/missing command."
         print(f"LOGIC: {message}")
         return {"success": False, "message": message}
         
    # Delegate execution to the existing single command runner
    logging.info(f"Running favorite '{name}' command: {command_to_run}")
    result = run_single_command_logic(command_to_run)
    # Add context that this was run from a favorite
    result['message'] = f"Ran favorite '{name}': {command_to_run}. Result: {result.get('message', 'Success' if result.get('success') else 'Failure')}"
    logging.debug(f"Exiting run_favorite_logic for '{name}', result: {result}")
    return result

# --- Location Logic Functions ---

def get_location_categories_logic():
    """Gets location categories from the data loader.

    Returns:
        dict: { "categories": { category_name: category_file, ... } }
              or { "categories": {} } on failure.
    """
    logging.debug("Entering get_location_categories_logic")
    try:
        categories = data_loader.get_location_categories()
        logging.debug(f"Exiting get_location_categories_logic with {len(categories)} categories.")
        return {"categories": categories}
    except Exception as e:
        logging.exception("Exception in get_location_categories_logic")
        return {"categories": {}}

def get_locations_in_category_logic(category_filename):
    """Gets locations for a specific category file from the data loader.

    Args:
        category_filename (str): The relative path to the category file (e.g., "locations/cities.json").

    Returns:
        dict: { "locations": { location_name: location_id, ... } }
              or { "locations": {} } on failure or invalid input.
    """
    logging.debug(f"Entering get_locations_in_category_logic for file: {category_filename}")
    if not category_filename or not isinstance(category_filename, str) or not category_filename.strip():
        logging.warning("Invalid category filename received in logic.")
        return {"locations": {}}
    try:
        locations = data_loader.load_locations_for_category(category_filename)
        logging.debug(f"Exiting get_locations_in_category_logic with {len(locations)} locations.")
        return {"locations": locations}
    except Exception as e:
        logging.exception("Exception in get_locations_in_category_logic")
        return {"locations": {}}

def teleport_to_location_logic(location_id):
    """Builds and executes a teleport command.

    Args:
        location_id (str): The target location ID (cell name).

    Returns:
        dict: { "success": bool, "message": str, "command": str or None }
    """
    logging.debug(f"Entering teleport_to_location_logic for ID: {location_id}")
    if not location_id or not isinstance(location_id, str) or not location_id.strip():
        logging.warning("Invalid location ID provided for teleport.")
        return {"success": False, "message": "Invalid location ID provided."}

    # Need to call it via the imported module
    command = command_builder.build_teleport_command(location_id)

    if not command:
        logging.error(f"Failed to build teleport command for ID: {location_id}")
        return {"success": False, "message": "Failed to build teleport command."}

    logging.info(f"Built teleport command: {command}")
    # Delegate to the single command execution logic
    result = run_single_command_logic(command)
    result['command'] = command # Add the command string to the result

    # Adjust message for clarity if successful
    if result['success']:
        result['message'] = "Teleport command executed."
        
    logging.debug(f"Exiting teleport_to_location_logic, result: {result}")
    return result 