# Placeholder for user interface logic 

from . import data_loader
from . import command_builder
import os
import platform

def clear_screen():
    """Clears the terminal screen."""
    os.system('cls' if platform.system() == "Windows" else 'clear')

# Sentinel object to indicate user chose 'Go Back'
# Using an object avoids confusion with None which might be a valid return in other contexts
class GoBack: pass
GO_BACK = GoBack()

def _get_numeric_input(prompt, min_val=None, max_val=None, allow_zero=False):
    """Gets and validates numeric input from the user."""
    while True:
        try:
            value_str = input(prompt).strip()
            value = int(value_str)

            is_valid = True
            err_msg = ""

            if value == 0 and allow_zero:
                return value # Allow zero if explicitly permitted

            if min_val is not None and value < min_val:
                is_valid = False
                err_msg = f"Minimum value is {min_val}."
            if max_val is not None and value > max_val:
                is_valid = False
                err_msg = f"Maximum value is {max_val}."
            if value <= 0 and not allow_zero:
                 is_valid = False # Implicitly disallow <= 0 unless allow_zero is True
                 if not err_msg: # Don't overwrite min/max message
                      err_msg = "Please enter a positive number."

            if is_valid:
                return value
            else:
                print(f"Invalid input. {err_msg}")

        except ValueError:
            print("Invalid input. Please enter a number.")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

def _select_from_list(items, prompt_prefix):
    """Displays a numbered list and gets the user's selection index.
       Returns the selected item or GO_BACK if the user chooses 0.
    """
    if not items:
        print("No items to select.")
        # Decide if this should trigger GO_BACK or be an error
        return None # Returning None might be better here than GO_BACK

    print(f"\n--- {prompt_prefix} Selection ---")
    item_map = {i + 1: item for i, item in enumerate(items)}
    print(" 0: Go Back") # Add Go Back option
    for i, item in item_map.items():
        if isinstance(item, tuple): # Handle (name, id) tuples for display
            print(f"{i:>2}: {item[0]} (ID: {item[1]})") # Right-align index
        else:
            print(f"{i:>2}: {item}") # Right-align index

    while True:
        choice = _get_numeric_input(
            f"Enter the number (0-{len(items)}): ",
            min_val=0, # Allow 0
            max_val=len(items),
            allow_zero=True # Explicitly allow 0
        )

        if choice == 0:
            return GO_BACK # Signal Go Back

        if choice in item_map:
            selected_item = item_map[choice]
            # Display selection more clearly
            selected_name = selected_item[0] if isinstance(selected_item, tuple) else selected_item
            print(f"--> Selected: {selected_name}")
            return selected_item
        else:
             print("Invalid selection number.") # Should not happen with validation

def _get_quantity(prompt="Enter the quantity (or 0 to go back): "):
    """Gets a positive quantity from the user, allows 0 for 'Go Back'."""
    value = _get_numeric_input(prompt, min_val=0, allow_zero=True)
    if value == 0:
        return GO_BACK
    return value

def handle_utility_commands():
    """Handles the selection of simple utility commands."""
    available_commands = ["ghost", "walk"]
    selected_command = _select_from_list(available_commands, "Utility Command")

    if selected_command is GO_BACK:
        return None # Propagate Go Back signal
    if selected_command:
        return command_builder.build_simple_command(selected_command)
    return None

def handle_npc_spawn():
    """Handles the NPC selection and command building."""
    npc_data = data_loader.load_json_data("npcs.json")
    if not npc_data:
        return None

    npc_list = list(npc_data.items()) # List of (name, id) tuples
    selected_npc = _select_from_list(npc_list, "NPC Spawn")

    if selected_npc is GO_BACK:
        return None # Propagate Go Back signal
    if selected_npc:
        npc_id = selected_npc[1]
        quantity = _get_quantity("Enter the number of NPCs to spawn (or 0 to go back): ")
        if quantity is GO_BACK:
            return None # Propagate Go Back signal
        return command_builder.build_placeatme_command(npc_id, quantity)
    return None

def handle_item_commands():
    """Handles item category selection, item selection, and command building."""
    item_categories = data_loader.get_item_categories()
    if not item_categories:
        print("No item categories found.")
        return None

    category_names = sorted(list(item_categories.keys())) # Sort categories for consistency
    selected_category_name = _select_from_list(category_names, "Item Category")

    if selected_category_name is GO_BACK:
        return None # Propagate Go Back signal
    if not selected_category_name:
        return None

    # Load data for the selected category
    filename = item_categories[selected_category_name]
    item_data = data_loader.load_json_data(filename)
    if not item_data:
        return None

    item_list = sorted(list(item_data.items())) # Sort items alphabetically by name
    selected_item = _select_from_list(item_list, selected_category_name)

    if selected_item is GO_BACK:
        return None # Propagate Go Back signal
    if selected_item:
        item_id = selected_item[1]
        quantity = _get_quantity("Enter the number of items to add (or 0 to go back): ")
        if quantity is GO_BACK:
            return None # Propagate Go Back signal
        return command_builder.build_additem_command(item_id, quantity)
    return None

def get_command_from_user():
    """Main menu logic to get the final command string from the user."""
    while True:
        clear_screen() # Clear screen at the start of each main menu display
        print("\n=============== Main Menu ===============") # Make menu title stand out
        print(" 1: Utility Commands")
        print(" 2: NPC Spawn")
        print(" 3: Add Items")
        print(" 0: Exit")
        print("=========================================")
        menu_choice = input("Select command type: ").strip()

        command_to_run = None
        if menu_choice == '1':
            command_to_run = handle_utility_commands()
        elif menu_choice == '2':
            command_to_run = handle_npc_spawn()
        elif menu_choice == '3':
            command_to_run = handle_item_commands()
        elif menu_choice == '0':
            print("Exiting.")
            return None # Signal exit
        else:
            print("Invalid choice. Please try again.")

        # If a handler returned None, it means the user chose 'Go Back' somewhere
        # or an error occurred loading data. The loop continues, showing the main menu again.
        if command_to_run:
            # print(f"\nCommand built: '{command_to_run}'") # Optional: Maybe too verbose now
            return command_to_run # Return the successfully built command
        else:
            print("Returning to main menu...") # Clarify why menu is re-showing
            # No need for print("---") here, loop continues naturally 