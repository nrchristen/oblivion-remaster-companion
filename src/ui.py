# Placeholder for user interface logic 

from . import data_loader
from . import command_builder
import os
import platform
# from inquirerpy import prompt # Remove inquirerpy import
# from inquirerpy.base.control import Choice # Remove inquirerpy import
import pick # Add pick import

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
    """Displays a list using pick and gets the user's selection.
       Returns the selected item's value or GO_BACK if the user chooses 'Go Back' or cancels.
    """
    if not items:
        print("No items to select.")
        return None

    title = f"--- {prompt_prefix} Selection (Use arrows, Enter to select) ---"
    options = []
    # Add "Go Back" option first, storing GO_BACK as the value
    options.append(("Go Back", GO_BACK))

    for item in items:
        if isinstance(item, tuple): # Handle (name, id) tuples
            options.append((f"{item[0]} (ID: {item[1]})", item)) # Display name, store original tuple
        else:
            options.append((str(item), item)) # Display item, store item

    try:
        clear_screen() # Clear screen before showing the prompt
        selected_option, index = pick.pick(
            [option[0] for option in options], # Pass only the display names
            title,
            indicator='*'
        )
        # Get the corresponding stored value (GO_BACK or the item/tuple)
        selected_value = options[index][1]

        # Optional: Print confirmation if not going back
        if selected_value is not GO_BACK:
            # selected_name = selected_option # The displayed name is already correct
            # print(f"--> Selected: {selected_name}") # Commented out as requested
            pass # Keep the if block structure, do nothing if not GO_BACK
        return selected_value

    except KeyboardInterrupt:
        return GO_BACK # Treat Ctrl+C as Go Back

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

def handle_preset_battle_selection():
    """Loads presets from battles.json and lets the user select one."""
    print("\n--- Preset Battle Selection ---")
    preset_data = data_loader.load_json_data("battles.json")

    if not preset_data:
        print("Error: Could not load battle presets from data/battles.json")
        input("Press Enter to go back...")
        return None

    preset_names = list(preset_data.keys())
    if not preset_names:
        print("No presets found in data/battles.json")
        input("Press Enter to go back...")
        return None

    # Use _select_from_list to choose a preset name
    selected_name = _select_from_list(preset_names, "Preset Battle")

    if selected_name is GO_BACK:
        return None # User chose Go Back
    
    if selected_name:
        # Return the list of commands associated with the selected name
        commands = preset_data.get(selected_name)
        if commands:
            print(f"Selected preset: {selected_name} ({len(commands)} commands)")
            return commands
        else:
            # Should not happen if selection works correctly
            print(f"Error: Could not retrieve commands for selected preset '{selected_name}'.")
            input("Press Enter to go back...")
            return None
    else:
        # _select_from_list returned None (e.g., error or empty list)
        print("No preset selected.")
        return None

def handle_battle_stage():
    """Handles the selection of multiple NPC groups for a battle stage setup."""
    all_battle_commands = []
    group_number = 1

    npc_data = data_loader.load_json_data("npcs.json")
    if not npc_data:
        print("Error: Cannot load npc data for Battle Stage.")
        return None
    npc_list = list(npc_data.items()) # List of (name, id) tuples

    while True:
        clear_screen()
        print(f"\n--- Battle Stage: Setup Group {group_number} ---")
        print(f"Current commands: {len(all_battle_commands)}")

        # Select NPC for this group
        selected_npc = _select_from_list(npc_list, f"NPC Group {group_number}")

        if selected_npc is GO_BACK:
            # If it's the first group and they go back, cancel the whole setup
            if group_number == 1:
                print("Battle Stage setup cancelled.")
                return None
            else:
                # Otherwise, assume they are finished setting up groups
                print("Finishing Battle Stage setup...")
                break # Exit the group setup loop

        if selected_npc:
            npc_id = selected_npc[1]
            # Get quantity, allowing Go Back to cancel adding *this* NPC
            quantity = _get_quantity(f"Enter number of '{selected_npc[0]}' for Group {group_number} (or 0 to cancel this NPC): ")
            
            if quantity is GO_BACK:
                print(f"Cancelled adding {selected_npc[0]} to Group {group_number}.")
                continue # Go back to selecting NPC for this group number
            
            if quantity > 0:
                command = command_builder.build_placeatme_command(npc_id, quantity)
                all_battle_commands.append(command)
                print(f"Added '{command}' to the battle plan.")
                group_number += 1 # Only increment group number if an NPC was successfully added
            else: # Should not happen due to _get_quantity logic, but safety check
                print("Quantity must be positive.")
                # Let user retry quantity for the same NPC
                input("Press Enter to retry quantity...") 
                continue 
        else:
            # Should not happen if _select_from_list works correctly unless npc_list is empty
            print("No NPC selected.") 
            continue

        # Ask to add another group *after* successfully adding one
        add_another = input("\nAdd another NPC group? (y/n): ").strip().lower()
        if add_another != 'y':
            break # Finished adding groups

    # Minimum check
    if len(all_battle_commands) < 1:
        print("No commands added for the Battle Stage.")
        return None

    print(f"\nCustom Battle setup complete with {len(all_battle_commands)} commands.")

    # --- Ask to Save Preset Start ---
    save_choice = input("Save this setup as a preset? (y/n): ").strip().lower()
    if save_choice == 'y':
        while True: # Loop for getting a valid preset name
            preset_name = input("Enter a name for this preset (leave blank to cancel save): ").strip()
            if not preset_name:
                print("Save cancelled.")
                break # Exit name loop
            
            # Attempt to save using the new data_loader function
            save_status = data_loader.add_battle_preset(preset_name, all_battle_commands)
            
            if save_status == "success":
                # Saved successfully, no need to ask again
                break # Exit name loop
            elif save_status == "exists":
                print(f"Error: Preset name '{preset_name}' already exists.")
                # Ask again for a different name
            elif save_status == "error":
                # data_loader printed the error, just inform user and ask again
                print("Could not save preset due to an error.")
                # Ask again
            
            # Ask if they want to try a different name if save failed/exists
            try_again = input("Try saving with a different name? (y/n): ").strip().lower()
            if try_again != 'y':
                 print("Save cancelled.")
                 break # Exit name loop
    # --- Ask to Save Preset End ---

    return all_battle_commands

def handle_battle_mode_entry():
    """Presents the entry menu for Battle Stage mode (Preset vs Custom)."""
    clear_screen()
    title = "--- Battle Stage Mode ---"
    options = [
        ("Select Preset Battle", "preset"),
        ("Custom Battle Setup", "custom"),
        ("Go Back", "back"),
    ]

    try:
        selected_option, index = pick.pick(
            [option[0] for option in options],
            title,
            indicator='*'
        )
        choice = options[index][1]
    except KeyboardInterrupt:
        choice = "back"

    battle_commands = None
    if choice == 'preset':
        battle_commands = handle_preset_battle_selection()
    elif choice == 'custom':
        # Call the function that handles custom NPC group selection
        battle_commands = handle_battle_stage()
    elif choice == 'back':
        return None # Go back to the main menu
    
    # Return the list of commands from the chosen sub-handler (or None if cancelled/not implemented)
    return battle_commands

def get_command_from_user():
    """Main menu logic using pick to get the command type for single/chain modes."""
    while True:
        clear_screen()
        # This menu should NOT have Battle Stage - that's handled by main.py's initial mode selection
        title = "=============== Select Command Type (for Single/Chain) ==============="
        options = [
            ("Utility Commands", "utility"),
            ("NPC Spawn", "npc"), # Single NPC spawn
            ("Add Items", "item"),
            ("Go Back", "exit"), # Changed value to 'exit' to match return expectation
        ]

        try:
            selected_option, index = pick.pick(
                [option[0] for option in options],
                title,
                indicator='*'
            )
            menu_choice = options[index][1]
        except KeyboardInterrupt:
            menu_choice = "exit"

        command_to_run = None
        if menu_choice == 'utility':
            command_to_run = handle_utility_commands()
        elif menu_choice == 'npc':
            command_to_run = handle_npc_spawn()
        elif menu_choice == 'item':
            command_to_run = handle_item_commands()
        # Removed battle case - it's handled in main.py
        elif menu_choice == 'exit':
            print("\nReturning to mode selection...")
            return None # Signal go back

        # This function now only returns a single command string or None
        if command_to_run:
            return command_to_run
        elif command_to_run is None and menu_choice != 'exit':
            # This means a sub-handler returned None (GO_BACK or data error)
            print("Returning to command type selection...")
            input("Press Enter to continue...")
        # Loop continues if a sub-handler returned None (meaning user chose Go Back within that handler) 