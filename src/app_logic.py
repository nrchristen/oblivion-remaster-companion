"""
Core application logic/service layer, independent of UI (GUI or CLI).
Handles interaction with automator, data loader, and command builder.
"""
import time

# Need to access the shared automator instance and game_found status.
# How to handle this? Pass them in? Use globals from app.py?
# Using globals is simpler for this structure but less SOLID.
# Let's import app and access its globals for now.
# A better approach would be dependency injection if complexity grew.
import app 

from src.data_loader import load_json_data, get_item_categories
from src.command_builder import build_additem_command

def check_game_status_logic():
    """Checks the current game status."""
    # Access global state from app.py
    status_msg = "Game Found" if app.game_found else "Game Not Found"
    return {"status": status_msg}

def run_single_command_logic(command):
    """Handles validation and execution for a single command string."""
    print(f"LOGIC: Executing single command: {command}")
    if not app.game_found:
        print("LOGIC: Game not found.")
        return {"success": False, "message": "Game not found"}
    if not command or not isinstance(command, str):
         print("LOGIC: Invalid command.")
         return {"success": False, "message": "Invalid command"}

    # Use the execute_command (full cycle) method from the shared automator
    success = app.automator.execute_command(command.strip(), verbose=False) # GUI/API usually non-verbose
    print(f"LOGIC: Single command execution result: {success}")
    return {"success": success}

def get_presets_logic(preset_type="battle"):
    """Loads presets of a given type (e.g., 'battle')."""
    filename = f"{preset_type}s.json" # Assumes plural naming convention
    print(f"LOGIC: Getting presets from {filename}...")
    preset_data = load_json_data(filename)
    if preset_data and isinstance(preset_data, dict):
        presets = list(preset_data.keys())
        print(f"LOGIC: Found presets: {presets}")
        return {"presets": presets}
    else:
        print(f"LOGIC: No presets found or error loading {filename}.")
        return {"presets": []}

def run_command_sequence_logic(commands, sequence_name="sequence"):
     """Opens console, runs a list of commands, closes console."""
     print(f"LOGIC: Running command {sequence_name} ({len(commands)} commands)...")
     if not app.game_found:
         print("LOGIC: Game not found.")
         return {"success": False, "message": "Game not found"}
     if not commands or not isinstance(commands, list):
          print("LOGIC: Invalid command list.")
          return {"success": False, "message": "Invalid command list"}

     all_succeeded = False
     # Use the shared automator instance
     if app.automator.open_console(verbose=False): # Non-verbose from logic layer usually
         all_succeeded = True
         for i, cmd in enumerate(commands):
             print(f"LOGIC: Executing {sequence_name} step {i+1}: {cmd}")
             success = app.automator.execute_command_in_console(cmd, verbose=False)
             if not success:
                 print(f"LOGIC: Command '{cmd}' failed in {sequence_name}. Stopping.")
                 all_succeeded = False
                 break
             time.sleep(0.5) # Keep delay between commands
         app.automator.close_console(verbose=False)
     else:
         print(f"LOGIC: Failed to open console for {sequence_name} execution.")
         all_succeeded = False
         
     print(f"LOGIC: {sequence_name} execution finished. Success: {all_succeeded}")
     return {"success": all_succeeded}

def run_preset_logic(preset_name, preset_type="battle"):
    """Loads a preset and runs its command sequence."""
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
    return run_command_sequence_logic(commands, sequence_name=f"preset '{preset_name}'")

def get_item_categories_logic():
    """Loads and returns item category names and filenames."""
    print("LOGIC: Getting item categories...")
    categories = get_item_categories() # Returns dict {name: filename}
    if categories:
        print(f"LOGIC: Found categories: {list(categories.keys())}")
        return {"categories": categories}
    else:
        print("LOGIC: No item categories found.")
        return {"categories": {}}

def get_items_in_category_logic(filename):
    """Loads items from a specific category file."""
    print(f"LOGIC: Getting items for category file: {filename}")
    if not filename or '..' in filename or filename.startswith('/') or filename.startswith('\\'):
        print("LOGIC: Invalid or potentially unsafe filename rejected.")
        return {"items": {}} # Return empty dict for invalid filename
        
    item_data = load_json_data(filename) # Returns dict {name: id} or None
    if item_data and isinstance(item_data, dict):
        sorted_items = dict(sorted(item_data.items()))
        print(f"LOGIC: Found {len(sorted_items)} items.")
        return {"items": sorted_items}
    else:
        print(f"LOGIC: No items found or error loading '{filename}'.")
        return {"items": {}}

def add_item_logic(item_id, quantity):
    """Builds and executes the additem command."""
    print(f"LOGIC: Adding item: ID={item_id}, Qty={quantity}")
    if not app.game_found:
        print("LOGIC: Game not found.")
        return {"success": False, "message": "Game not found"}
    
    try:
        qty = int(quantity)
        if qty <= 0:
            raise ValueError("Quantity must be positive")
    except (ValueError, TypeError):
        print(f"LOGIC: Invalid quantity received: {quantity}")
        return {"success": False, "message": "Invalid quantity"}
    if not item_id or not isinstance(item_id, str):
        print(f"LOGIC: Invalid item ID received: {item_id}")
        return {"success": False, "message": "Invalid item ID"}

    command_string = build_additem_command(item_id, qty)
    print(f"LOGIC: Built command: {command_string}")
    
    # Delegate to single command logic (which uses execute_command full cycle)
    return run_single_command_logic(command_string) 