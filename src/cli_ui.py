"""
Handles the Command Line Interface (CLI) user interactions and flow.
"""
import sys
import os
import time
import pick
import itertools
import win32gui
import win32api
import win32console
import colorama
from colorama import Fore, Back, Style

# Assuming app_logic uses the global automator from app.py
# Need to import app_logic functions
from src import app_logic 
# Need UI functions originally from src.ui (we'll assume they exist here for now)
# Ideally, these would be imported from src.ui or moved here if purely console
from src.ui import get_command_from_user, handle_battle_mode_entry, clear_screen

# Use colorama constants defined in app.py or redefine?
# Let's redefine for isolation, though constants file is better.
COLOR_RESET = Style.RESET_ALL

def display_loading_animation(stop_event):
    """Displays a simple rotating spinner animation in the console."""
    spinner = itertools.cycle(['-', '\\', '|', '/'])
    while not stop_event.is_set():
        try:
            sys.stdout.write(f"\rSearching... {next(spinner)}")
            sys.stdout.flush()
            time.sleep(0.1)
        except Exception:
            break
    sys.stdout.write('\r' + ' ' * 20 + '\r')
    sys.stdout.flush()

def refocus_companion(hwnd):
    """Attempts to bring the companion console window to the foreground."""
    if not hwnd:
        return
    try:
        time.sleep(0.1)
        win32gui.SetForegroundWindow(hwnd)
        time.sleep(0.1)
    except Exception as e:
        pass

def run_companion_cli():
    """Main function for the console interface."""
    original_title = "ES4Companion (CLI)"
    os.system(f"title {original_title}")
    companion_hwnd = win32console.GetConsoleWindow()
    clear_screen()
    print("--- Elder Scrolls IV: Oblivion Companion (CLI) ---")
    print("Initializing...")
    
    # Check initial game status via logic layer
    status_result = app_logic.check_game_status_logic()
    if status_result["status"] != "Game Found":
        print("Game process and window not found.")
        print("Please ensure the game is running and restart the companion.")
        input("Press Enter to exit.")
        return
        
    print("Game process and window located successfully.")
    active_title = "ES4Companion (CLI) - Active (Connected to Game)"
    os.system(f"title {active_title}")

    while True:
        clear_screen()
        title = "--- Select Mode (Use arrows, Enter to select) ---"
        options = [
            ("Run Single Command", "single"),
            ("Build Command Chain", "chain"),
            ("Battle Stage Setup", "battle"),
            ("Exit", "exit"),
        ]
        try:
            selected_option, index = pick.pick(
                [option[0] for option in options],
                title,
                indicator='* '
            )
            mode = options[index][1]
        except KeyboardInterrupt:
            mode = "exit"
        print(COLOR_RESET)

        if mode == "exit":
            print("\nExiting.")
            os.system(f"title {original_title} - Exited")
            return

        result = None
        if mode == 'single':
            command_string = get_command_from_user() # UI layer gets the command
            if command_string:
                result = app_logic.run_single_command_logic(command_string) # Logic layer executes
                refocus_companion(companion_hwnd)
            continue # Always loop back immediately after single mode

        elif mode == 'chain':
            print("\n--- Command Chain Mode ---")
            command_chain = []
            while True:
                command_string = get_command_from_user()
                if command_string:
                    command_chain.append(command_string)
                    print(f"\nCommand '{command_string}' added to chain ({len(command_chain)} total).")
                    add_another = input("Add another command to the chain? (y/n): ").strip().lower()
                    if add_another != 'y':
                        break
                else:
                    print("Exiting command selection.")
                    break
            if not command_chain:
                print("\nNo commands in the chain to execute.")
            else:
                # Execute the sequence using the logic layer
                result = app_logic.run_command_sequence_logic(command_chain, "chain")
                # Print success/failure based on result?
                if result and result.get("success"): print("Chain finished successfully.")
                else: print("Chain finished with errors or could not start.")

            refocus_companion(companion_hwnd)
            input("\nPress Enter to return to the main menu...")

        elif mode == 'battle':
            # Battle mode entry handles preset vs custom via UI
            battle_commands = handle_battle_mode_entry()
            if not battle_commands:
                print("Battle setup cancelled or not implemented yet.")
            else:
                # Execute the sequence using the logic layer
                result = app_logic.run_command_sequence_logic(battle_commands, "battle stage")
                if result and result.get("success"): print("Battle stage finished successfully.")
                else: print("Battle stage finished with errors or could not start.")
                
            refocus_companion(companion_hwnd)
            input("\nPress Enter to return to the main menu...") 