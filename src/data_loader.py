# Placeholder for data loading logic 

import json
import os
import sys # Added
import logging
from typing import Dict, List, Optional

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
NPCS_FILE = "npcs.json" # Added constant for NPC file
LOCATION_CATEGORIES_FILE = "location_categories.json" # Removed path join here
LOCATIONS_SUBDIR = "locations"
LOCATIONS_DIR = os.path.join(DATA_DIR, LOCATIONS_SUBDIR) # Define full path separately

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
    """Loads item categories and their filenames from the ITEM_CATEGORIES_FILE."""
    logging.debug(f"Loading item categories from {ITEM_CATEGORIES_FILE}")
    categories = load_json_data(ITEM_CATEGORIES_FILE)

    if isinstance(categories, dict):
        logging.info(f"Loaded {len(categories)} item categories.")
        return categories
    else:
        logging.error(f"Failed to load or parse {ITEM_CATEGORIES_FILE}. Expected a JSON object.")
        return {} # Return empty dict on failure

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
        # Ensure the target directory exists
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR, exist_ok=True)
    except OSError as e:
        logging.error(f"Could not create directory {DATA_DIR}: {e}")
        print(f"Error: Could not create directory {DATA_DIR}.")
        return False # Return False if directory creation fails

    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2) # Use indent for readability
        logging.debug(f"Successfully saved data to {filepath}") # Changed to debug
        return True
    except IOError as e:
        logging.error(f"Error saving data to {filepath}: {e}")
        print(f"Error: Could not write to file {filepath}. Check permissions.")
    except TypeError as e:
        # Slightly adjust log message to match test expectation more closely
        logging.error(f"Error serializing data for {filepath}: {e}")
        print(f"Error: Could not serialize data for {filepath}.")
    except Exception as e:
        logging.exception(f"An unexpected error occurred saving {filepath}")
        print(f"An unexpected error occurred saving {filepath}.")
    
    return False # Return False for any exception during open/dump

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

def load_items_for_category(category_name: str) -> Optional[Dict[str, dict]]:
    """Loads item data for a specific category from its JSON file."""
    logger.debug(f"Attempting to load items for category: {category_name}")
    try:
        categories = get_item_categories()
        if category_name not in categories:
            logger.error(f"Category '{category_name}' not found in item categories map.")
            return None

        relative_filepath = categories[category_name]
        # Handle nested categories (subdirectories)
        filepath = os.path.join(DATA_DIR, relative_filepath)

        if not os.path.exists(filepath):
            logger.error(f"Data file not found for category '{category_name}' at path: {filepath}")
            return None

        with open(filepath, 'r') as f:
            data = json.load(f)
            logger.debug(f"Successfully loaded {len(data)} items for category '{category_name}' from {filepath}")
            return data
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON for category '{category_name}' from {filepath}: {e}")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred loading items for category '{category_name}': {e}")
        return None

# --- Location Loading ---
def get_location_categories():
    """Loads the mapping of location category names to their filenames.

    Returns:
        dict: A dictionary mapping category names (e.g., "Cities") 
              to their relative file paths (e.g., "locations/cities.json"), 
              sorted by category name. Returns an empty dict on error.
    """
    # Ensure the path uses DATA_DIR dynamically
    category_file_path = os.path.join(DATA_DIR, LOCATION_CATEGORIES_FILE) 
    logging.debug(f"Attempting to load location categories from: {category_file_path}")
    categories = load_json_data(LOCATION_CATEGORIES_FILE) 
    if not categories or not isinstance(categories, dict):
        logging.error(f"Failed to load or parse location categories from {LOCATION_CATEGORIES_FILE}. Expected a JSON object.")
        return {}
    
    # Prepend the locations subdirectory to each filename
    prefixed_categories = {name: os.path.join(LOCATIONS_SUBDIR, filename).replace("\\", "/")
                           for name, filename in categories.items()}
    
    # Sort by category name
    sorted_categories = dict(sorted(prefixed_categories.items()))
    logging.info(f"Loaded {len(sorted_categories)} location categories.")
    return sorted_categories

def load_locations_for_category(category_filename):
    """Loads location names and IDs from a specific category file.

    The filename should be relative to the DATA_DIR (e.g., "locations/cities.json").

    Args:
        category_filename (str): The relative path to the category JSON file 
                                 (e.g., "locations/cities.json").

    Returns:
        dict: A dictionary mapping location names to location IDs for the 
              given category, sorted by location name. Returns an empty dict on error 
              or if the file doesn't contain a valid dictionary.
    """
    if not category_filename or not isinstance(category_filename, str):
        logging.warning("Invalid category filename provided for loading locations.")
        return {}
        
    logging.debug(f"Attempting to load locations from category file: {category_filename}")
    # load_json_data already joins with DATA_DIR
    location_data = load_json_data(category_filename) 
    
    if not location_data or not isinstance(location_data, dict):
        # Log error if load_json_data didn't already (e.g., if file had a list)
        if location_data is not None: # Check if load succeeded but wasn't a dict
            logging.error(f"Invalid data format in {category_filename}. Expected a JSON object (dict).")
        # load_json_data logs errors for file not found or JSON decode errors
        return {}
    
    # Sort by location name
    sorted_locations = dict(sorted(location_data.items()))
    logging.info(f"Loaded {len(sorted_locations)} locations from {category_filename}.")
    return sorted_locations

# Initialize logger (assuming logger is already set up elsewhere in the project)
logger = logging.getLogger(__name__)
# Basic config if run standalone or logger not configured
if not logger.hasHandlers():
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Example usage (optional, for testing)
if __name__ == "__main__":
    print("Item Categories:", get_item_categories())
    # print("Arrows:", load_items_for_category("Arrows"))
    print("\nLocation Categories:", get_location_categories())
    print("Cities:", load_locations_for_category("Cities"))
    print("Guilds:", load_locations_for_category("Guild Halls"))
    print("Invalid Category:", load_locations_for_category("Invalid Category"))
    print("Non-existent File Category:", load_locations_for_category("Towns & Settlements")) # Assuming this file doesn't exist yet 

def load_all_locations(locations_dir=LOCATIONS_DIR):
    """Loads all location data from JSON files in the specified directory."""
    all_locations = {}
    if not os.path.isdir(locations_dir):
        logging.error(f"Locations directory not found: {locations_dir}")
        return all_locations

    try:
        for filename in os.listdir(locations_dir):
            if filename.endswith('.json'):
                file_path = os.path.join(locations_dir, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if isinstance(data, dict):
                            # Check for duplicate keys before merging
                            duplicates = set(data.keys()) & set(all_locations.keys())
                            if duplicates:
                                logging.warning(f"Duplicate location keys found in {filename} ignored: {duplicates}")
                            # Add only non-duplicate keys
                            all_locations.update({k: v for k, v in data.items() if k not in duplicates})
                        else:
                            logging.warning(f"Skipping {filename}: Content is not a JSON object (dict).")
                except json.JSONDecodeError:
                    logging.error(f"Error loading JSON from {filename}: Invalid format.")
                except Exception as e:
                    logging.error(f"Error reading file {filename}: {e}")
    except Exception as e:
        logging.error(f"Error listing files in directory {locations_dir}: {e}")

    # Sort the final dictionary by location name (key)
    sorted_locations = dict(sorted(all_locations.items()))
    logging.info(f"Loaded {len(sorted_locations)} locations from {locations_dir}")
    return sorted_locations

# --- Example usage (can be removed or kept for direct script testing) ---
if __name__ == '__main__':
    locations = load_all_locations()
    print("Loaded Locations:")
    # Pretty print the dictionary
    for name, loc_id in locations.items():
        print(f"  - {name}: {loc_id}") 

def get_preset_commands(preset_name, preset_type="battle"):
    """Placeholder for loading commands for a specific preset."""
    # TODO: Implement actual logic to load from appropriate file (e.g., battles.json)
    logging.warning(f"get_preset_commands not fully implemented. Called for: {preset_name}")
    # Example structure if loading from battles.json:
    # filename = f"{preset_type}s.json"
    # preset_data = load_json_data(filename)
    # if preset_data and isinstance(preset_data, dict) and preset_name in preset_data:
    #     return preset_data[preset_name]
    return None # Return None if not found or error

def find_data_file(filename):
    """Placeholder for finding a data file."""
    # TODO: Implement logic to find the file, possibly checking multiple locations.
    logging.warning(f"find_data_file not implemented. Called for: {filename}")
    filepath = os.path.join(DATA_DIR, filename)
    if os.path.exists(filepath):
        return filepath
    return None

def list_json_files(directory):
    """Placeholder for listing JSON files in a directory."""
    # TODO: Implement actual logic if needed by any feature.
    logging.warning(f"list_json_files not implemented. Called for: {directory}")
    return []

# --- NPC Loading --- 
def load_npcs():
    """Placeholder for loading NPCs."""
    # TODO: Implement actual logic if needed.
    logging.warning(f"load_npcs not implemented.")
    filename = NPCS_FILE # Use the constant
    npc_data = load_json_data(filename)
    if npc_data and isinstance(npc_data, dict):
        return npc_data
    return {}

# --- NPC Loading --- 