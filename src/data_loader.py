# Placeholder for data loading logic 

import json
import os
import sys # Added
import logging

# Determine base path for data files (works for script and frozen exe)
if getattr(sys, 'frozen', False):
    # Running as a bundled executable (PyInstaller)
    BASE_DIR = sys._MEIPASS
else:
    # Running as a normal script
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

DATA_DIR = os.path.join(BASE_DIR, 'data') # Adjusted path

ITEM_CATEGORIES_FILE = "item_categories.json"
BATTLES_FILE = "battles.json"
FAVORITES_FILE = "favorites.json" # Added constant

def load_json_data(filename):
    """Loads data from a JSON file in the data directory."""
    filepath = os.path.join(DATA_DIR, filename) # Uses the adjusted DATA_DIR
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            logging.debug(f"Successfully loaded data from {filename}")
            return data
    except FileNotFoundError:
        logging.error(f"Data file not found at {filepath}")
        return None
    except json.JSONDecodeError:
        logging.error(f"Could not decode JSON from {filepath}. Check for syntax errors.")
        return None
    except Exception as e:
        logging.exception(f"An unexpected error occurred loading {filename}")
        return None

def get_item_categories():
    """Returns a dictionary of available item categories and their filenames.
       Only includes categories whose corresponding JSON files can be loaded successfully.
    """
    categories = {}
    # Define files that are NOT item categories (NPCs, saved Battles)
    exclude_files = {'npcs.json', 'battles.json'} # Removed 'locations.json'
    try:
        for filename in os.listdir(DATA_DIR):
            # Check if it's a JSON file and not in the exclusion list
            if filename.lower().endswith('.json') and filename.lower() not in exclude_files:
                # Convert filename (e.g., "alchemy_equipment.json") to category name ("Alchemy equipment")
                category_name = filename[:-5].replace('_', ' ').replace('-', ' ').capitalize()
                
                # Basic check to see if the file can be loaded as a dict (implies item data structure)
                # This is optional but adds robustness
                data = load_json_data(filename)
                if isinstance(data, dict):
                     categories[category_name] = filename
                else:
                     print(f"INFO: Skipping category for file '{filename}' due to loading errors or non-dict format.")
                    
    except FileNotFoundError:
        print(f"Error: Data directory not found at {DATA_DIR}")
    except Exception as e:
        print(f"Error listing item categories: {e}")
    return categories 

def save_json_data(filename, data):
    """Saves the provided Python object (dict/list) to a JSON file.

    Args:
        filename (str): The name of the file (relative to DATA_DIR).
        data: The Python object to serialize and save.

    Returns:
        bool: True if saving was successful, False otherwise.
    """
    filepath = os.path.join(DATA_DIR, filename)
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2) # Use indent for readability
        logging.info(f"Successfully saved data to {filepath}")
        return True
    except IOError as e:
        logging.error(f"Error saving data to {filepath}: {e}")
        print(f"Error: Could not write to file {filepath}. Check permissions.")
    except TypeError as e:
        logging.error(f"Error serializing data for {filepath}: {e}")
        print(f"Error: Could not serialize data for {filepath}.")
    except Exception as e:
        logging.exception(f"An unexpected error occurred saving {filepath}")
        print(f"An unexpected error occurred saving {filepath}.")
    return False

def add_battle_preset(preset_name, command_list):
    """Adds a new battle preset to battles.json.

    Args:
        preset_name (str): The name for the new preset.
        command_list (list): The list of command strings for the preset.

    Returns:
        str: "success" if saved, "exists" if name already exists, "error" otherwise.
    """
    if not preset_name or not isinstance(preset_name, str) or not preset_name.strip():
        print("Error: Preset name cannot be empty.")
        return "error"
    if not command_list or not isinstance(command_list, list):
        print("Error: Invalid command list provided.")
        return "error"

    filename = "battles.json"
    presets = load_json_data(filename)
    
    # Handle case where file doesn't exist or is empty/invalid
    if presets is None:
        presets = {} # Start fresh if loading failed
    elif not isinstance(presets, dict):
        print(f"Error: Existing {filename} does not contain a valid JSON object. Cannot add preset.")
        # Consider backing up the invalid file here?
        return "error"

    preset_name = preset_name.strip()
    if preset_name in presets:
        # print(f"Error: Preset name '{preset_name}' already exists.")
        logging.warning(f"Preset name '{preset_name}' already exists.")
        return "exists" # Signal that the name exists

    # Add the new preset
    presets[preset_name] = command_list

    # Save the updated dictionary
    if save_json_data(filename, presets):
        # print(f"Preset '{preset_name}' saved successfully to {filename}.")
        logging.info(f"Preset '{preset_name}' saved successfully to {filename}.")
        return "success"
    else:
        # save_json_data would have printed an error
        return "error" 

# --- Initialization --- 
def ensure_data_files_exist():
    """Ensure essential data files exist, creating empty ones if needed."""
    required_files = {
        ITEM_CATEGORIES_FILE: {},
        BATTLES_FILE: {},
        FAVORITES_FILE: [] # Favorites should be a list
    }
    os.makedirs(DATA_DIR, exist_ok=True)
    for filename, default_content in required_files.items():
        filepath = os.path.join(DATA_DIR, filename)
        if not os.path.exists(filepath):
            logging.warning(f"Data file not found: {filepath}. Creating empty file.")
            if not save_json_data(filename, default_content):
                logging.error(f"Failed to create default data file: {filepath}")
                # Decide if this is fatal? For now, just log error.

# Call this on module load or explicitly from app startup
ensure_data_files_exist() 