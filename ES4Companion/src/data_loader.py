# Placeholder for data loading logic 

import json
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')

def load_json_data(filename):
    """Loads data from a JSON file in the data directory."""
    filepath = os.path.join(DATA_DIR, filename)
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
    excluded_files = ['npcs.json']
    categories = {}
    try:
        for filename in os.listdir(DATA_DIR):
            if filename.endswith('.json') and filename not in excluded_files:
                # Attempt to load the data to ensure the file is valid
                if load_json_data(filename) is not None:
                    # Derive category name from filename (e.g., arrows.json -> Arrows)
                    category_name = os.path.splitext(filename)[0].replace('_', ' ').capitalize()
                    categories[category_name] = filename
                else:
                    # Optionally log that a file was skipped due to loading errors
                    print(f"INFO: Skipping category for file '{filename}' due to loading errors.")

    except FileNotFoundError:
        print(f"Error: Data directory not found at {DATA_DIR}")
    except Exception as e:
        print(f"Error listing item categories: {e}")
    return categories 