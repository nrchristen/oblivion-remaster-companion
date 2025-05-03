import sys
import os
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import configparser
import subprocess
import logging # Add logging
import traceback # Add traceback
import pick # Add this import
import threading # Add threading
import itertools # Add itertools for cycling
import win32gui # Add win32gui
import win32api # Add win32api
import win32console # Add win32console

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.automator import WindowAutomator
from src.ui import get_command_from_user, clear_screen, handle_battle_mode_entry

TARGET_EXECUTABLE = "OblivionRemastered-WinGDK-Shipping.exe"

# --- Setup Logging Start ---
log_file = 'companion_log.txt'
try:
    # Basic logging config - write to a file
    logging.basicConfig(
        level=logging.DEBUG, # Log everything from DEBUG level up
        format='%(asctime)s - %(levelname)s - %(message)s',
        filename=log_file,
        filemode='w' # Overwrite log file each time
    )
    logging.info("--- Application Starting ---")
except Exception as log_setup_e:
    # If logging setup fails, we can't log, try a message box
    try:
        import tkinter as tk_err
        from tkinter import messagebox as messagebox_err
        root_err = tk_err.Tk()
        root_err.withdraw()
        messagebox_err.showerror("Fatal Logging Error", f"Could not set up logging:\n{log_setup_e}")
        root_err.destroy()
    except Exception:
        pass # No GUI possible if Tkinter itself fails
    exit(1) # Exit if logging cannot be set up
# --- Setup Logging End ---

# --- Animation Function Start ---
def display_loading_animation(stop_event):
    """Displays a simple rotating spinner animation in the console."""
    spinner = itertools.cycle(['-', '\\', '|', '/'])
    while not stop_event.is_set():
        try:
            # Print next spinner frame, overwrite previous line, no newline
            sys.stdout.write(f"\rSearching... {next(spinner)}")
            sys.stdout.flush() # Ensure it's written immediately
            time.sleep(0.1) # Control animation speed
        except Exception:
            # Handle potential errors writing to stdout if console is closed etc.
            break
    # Clear the animation line when done
    sys.stdout.write('\r' + ' ' * 20 + '\r') # Overwrite with spaces
    sys.stdout.flush()
# --- Animation Function End ---

# --- Helper to Refocus Console --- 
def refocus_companion(hwnd):
    """Attempts to bring the companion console window to the foreground."""
    if not hwnd:
        return
    try:
        # Small delay before trying to refocus
        time.sleep(0.1)
        win32gui.SetForegroundWindow(hwnd)
        time.sleep(0.1)
    except Exception as e:
        # Log this? For now, fail silently if refocus fails.
        # print(f"Warning: Could not refocus companion window: {e}") 
        pass

def run_companion():
    """Main function to run the ES4 Companion tool."""
    original_title = "ES4Companion"
    os.system(f"title {original_title}")
    # Get companion console HWND using win32console
    companion_hwnd = win32console.GetConsoleWindow()
    clear_screen()
    print("--- Elder Scrolls IV: Oblivion Companion ---")
    print("Initializing...")

    automator = WindowAutomator(TARGET_EXECUTABLE)

    # --- Start Animation and Search --- 
    stop_event = threading.Event()
    animation_thread = threading.Thread(
        target=display_loading_animation, 
        args=(stop_event,), 
        daemon=True # Allow program to exit even if thread is running
    )
    animation_thread.start()

    found = False
    try:
        # This function prints "Looking for process..."
        found = automator.find_process_and_window()
    finally:
        # Ensure animation stops regardless of success/failure/error
        stop_event.set()
        # animation_thread.join() # Wait briefly? Daemon thread should exit anyway
        # Give a tiny moment for the clearing print in the animation thread to run
        time.sleep(0.1) 
    # --- End Animation and Search --- 

    if not found:
        # Error message already printed by find_process_and_window
        # print("\nFailed to find running game process or window.")
        # print("Please ensure the game is running and try again.")
        input("Press Enter to exit.")
        return

    # If found, automator doesn't print success, so we do
    print("Game process and window located successfully.")

    active_title = "ES4Companion - Active (Connected to Game)"
    os.system(f"title {active_title}")
    # print("\nGame window located successfully.") # Moved up

    # --- Main Application Loop ---
    while True:
        # --- Mode Selection --- (Using pick)
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
                indicator='*'
            )
            mode = options[index][1]
        except KeyboardInterrupt:
            mode = "exit"

        if mode == "exit":
            print("\nExiting.")
            os.system(f"title {original_title} - Exited")
            return

        # --- Command Execution Logic ---
        if mode == 'single':
            command_string = get_command_from_user()
            if command_string:
                # Use the original execute_command (now an alias for execute_single_command)
                success = automator.execute_command(command_string, verbose=False)
                refocus_companion(companion_hwnd)
            continue

        elif mode == 'chain':
            print("\n--- Command Chain Mode ---")
            command_chain = []
            while True:
                # Call get_command_from_user to select command type for next chain link
                command_string = get_command_from_user()
                if command_string:
                    command_chain.append(command_string)
                    print(f"\nCommand '{command_string}' added to chain ({len(command_chain)} total).")
                    add_another = input("Add another command to the chain? (y/n): ").strip().lower()
                    if add_another != 'y':
                        break # Finished adding commands
                else:
                    # User chose Go Back in get_command_from_user
                    print("Exiting command selection.")
                    break
            # Execute the chain
            if not command_chain:
                print("\nNo commands in the chain to execute.")
            else:
                print(f"\n--- Preparing Command Chain ({len(command_chain)} commands) ---")
                # Open console ONCE before the loop
                if automator.open_console(verbose=True):
                    all_succeeded = True
                    for i, cmd in enumerate(command_chain):
                        print(f"\nExecuting command {i+1}/{len(command_chain)}:") # Removed cmd from here
                        # Execute command assuming console is open
                        success = automator.execute_command_in_console(cmd, verbose=True)
                        if not success:
                            print(f"Command {i+1} failed or was aborted. Stopping chain.")
                            all_succeeded = False
                            break # Stop chain on failure
                        
                        # Optional shorter delay between commands in chain?
                        if i < len(command_chain) - 1:
                            time.sleep(0.5) # Shorter pause within chain
                    
                    # Close console ONCE after the loop
                    automator.close_console(verbose=True)
                    
                    if all_succeeded:
                        print("\n--- Command Chain Execution Finished Successfully ---")
                    else:
                        print("\n--- Command Chain Execution Finished with Errors ---")
                else:
                    print("Error: Could not open game console to start command chain.")
            
            refocus_companion(companion_hwnd)
            input("\nPress Enter to return to the main menu...")

        elif mode == 'battle':
            battle_commands = handle_battle_mode_entry()
            if not battle_commands:
                print("Battle setup cancelled or not implemented yet.")
            else:
                print(f"\n--- Preparing Battle Stage ({len(battle_commands)} commands) ---")
                # Open console ONCE before the loop
                if automator.open_console(verbose=True):
                    all_succeeded = True
                    for i, cmd in enumerate(battle_commands):
                        print(f"\nExecuting command {i+1}/{len(battle_commands)}:") # Removed cmd
                        # Execute command assuming console is open
                        success = automator.execute_command_in_console(cmd, verbose=True)
                        if not success:
                            print(f"Command {i+1} failed or was aborted. Stopping battle setup.")
                            all_succeeded = False
                            break # Stop on failure
                        
                        # Optional shorter delay between commands?
                        if i < len(battle_commands) - 1:
                           time.sleep(0.5) # Shorter pause within battle stage
                           
                    # Close console ONCE after the loop
                    automator.close_console(verbose=True)
                    
                    if all_succeeded:
                        print("\n--- Battle Stage Execution Finished Successfully ---")
                    else:
                        print("\n--- Battle Stage Execution Finished with Errors ---")
                else:
                     print("Error: Could not open game console to start battle stage.")

            refocus_companion(companion_hwnd)
            input("\nPress Enter to return to the main menu...")

        # Loop continues to show main menu

    # --- End Main Application Loop ---

    # Removed the final clear_screen and print("Exiting...") here
    # as the exit now happens via return in the mode selection


if __name__ == "__main__":
    try:
        logging.info("Initializing main application.")
        # Add time import for chain delay
        print("INFO: Ensure this script is run with administrator privileges if the game requires them.")
        run_companion()
        logging.info("run_companion() finished.")

    except Exception as e:
        logging.error("An unhandled exception occurred:", exc_info=True) # Log the full traceback
        # Try to show an error message box
        try:
            root_err = tk.Tk()
            root_err.withdraw() # Hide the blank Tk window
            traceback_str = traceback.format_exc()
            error_message = f"A critical error occurred:\n\n{e}\n\nSee {log_file} for detailed traceback."
            # Limit message length for messagebox
            if len(traceback_str) > 1000:
                error_message = f"A critical error occurred:\n\n{e}\n\nTraceback (see {log_file} for full details):\n{traceback_str[:1000]}..."
            messagebox.showerror("Application Error", error_message)
            root_err.destroy()
        except Exception as inner_e:
            logging.error(f"Could not display error message box: {inner_e}")
        finally:
            logging.info("--- Application Terminating Due to Error ---")
            exit(1) # Exit with an error code
    finally:
        # This runs whether there was an exception or not (on normal exit)
        logging.info("--- Application Exiting Normally ---")
