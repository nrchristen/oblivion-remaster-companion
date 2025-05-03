# Placeholder for data loading logic 

import json
import os
import sys # Added

# Determine base path for data files (works for script and frozen exe)
if getattr(sys, 'frozen', False):
    # Running as a bundled executable (PyInstaller)
    BASE_DIR = sys._MEIPASS
else:
    # Running as a normal script
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

DATA_DIR = os.path.join(BASE_DIR, 'data') # Adjusted path

def load_json_data(filename):
    """Loads data from a JSON file in the data directory."""
    filepath = os.path.join(DATA_DIR, filename) # Uses the adjusted DATA_DIR
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            print(f"Successfully loaded {len(data)} entries from {filename}")
            return data
    except FileNotFoundError:
        print(f"Error: Data file not found at {filepath}")
        return None
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {filepath}. Check for syntax errors.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred loading {filename}: {e}")
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
    """Saves the provided data dictionary to a JSON file in the data directory.

    Args:
        filename (str): The name of the file (e.g., 'battles.json').
        data (dict): The dictionary data to save.

    Returns:
        bool: True if saving was successful, False otherwise.
    """
    filepath = os.path.join(DATA_DIR, filename)
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2) # Use indent for readability
        return True
    except IOError as e:
        print(f"Error saving data to {filepath}: {e}")
        return False
    except TypeError as e:
        print(f"Error serializing data for {filepath}: {e}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred saving {filepath}: {e}")
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
        return "exists" # Signal that the name exists

    # Add the new preset
    presets[preset_name] = command_list

    # Save the updated dictionary
    if save_json_data(filename, presets):
        print(f"Preset '{preset_name}' saved successfully to {filename}.")
        return "success"
    else:
        # save_json_data would have printed an error
        return "error" 