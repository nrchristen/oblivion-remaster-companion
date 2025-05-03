import sys
import os
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import configparser
import subprocess
import logging # Add logging
import traceback # Add traceback

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.automator import WindowAutomator
from src.ui import get_command_from_user, clear_screen

TARGET_EXECUTABLE = "OblivionRemastered-WinGDK-Shipping.exe"

# Angled Medieval Sword ASCII Art
SWORD_ART = r"""
          />
         //>
        // >
 ______//  >
 \     /> =================>
  \   //==================>
   \ //>=================>
    \/>
"""

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

def run_companion():
    """Main function to run the ES4 Companion tool."""
    original_title = "ES4Companion"
    os.system(f"title {original_title}")
    clear_screen()
    print(SWORD_ART)
    print("--- Elder Scrolls IV: Oblivion Companion ---")
    print("Initializing...")

    automator = WindowAutomator(TARGET_EXECUTABLE)

    if not automator.find_process_and_window():
        print("\nFailed to find running game process or window.")
        print("Please ensure the game is running and try again.")
        input("Press Enter to exit.")
        return

    active_title = "ES4Companion - Active (Connected to Game)"
    os.system(f"title {active_title}")
    print("\nGame window located successfully.")

    # --- Mode Selection --- (New)
    mode = None
    while mode is None:
        clear_screen()
        print("\n--- Select Mode ---")
        print("1: Run Single Command (then exit)")
        print("2: Build Command Chain (run multiple commands)")
        print("0: Exit")
        choice = input("Enter mode choice: ").strip()
        if choice == '1':
            mode = 'single'
        elif choice == '2':
            mode = 'chain'
        elif choice == '0':
            print("Exiting.")
            os.system(f"title {original_title} - Exited")
            return
        else:
            input("Invalid choice. Press Enter to try again.") # Pause for user
    # --- End Mode Selection ---


    # --- Command Execution Logic --- (Modified)
    if mode == 'single':
        print("\n--- Single Command Mode ---")
        command_string = get_command_from_user() # Get one command
        if command_string:
            print("\nAttempting to execute command...")
            if automator.execute_command(command_string):
                print("Command sequence completed successfully.")
            else:
                print("Command sequence failed or was aborted.")
        else:
            print("No command selected.")
        # Single mode exits after one attempt

    elif mode == 'chain':
        print("\n--- Command Chain Mode ---")
        command_chain = []
        while True:
            # Pass context to UI function (optional, but good practice)
            command_string = get_command_from_user() # Returns None on Exit/Go Back from Main Menu

            if command_string:
                command_chain.append(command_string)
                print(f"\nCommand '{command_string}' added to chain ({len(command_chain)} total).")
                add_another = input("Add another command to the chain? (y/n): ").strip().lower()
                if add_another != 'y':
                    break # Finished adding commands
            else:
                # User chose Exit or Go Back from main menu
                print("Exiting command selection.")
                break # Exit collection loop

        # Execute the chain
        if not command_chain:
            print("\nNo commands in the chain to execute.")
        else:
            print(f"\n--- Executing Command Chain ({len(command_chain)} commands) ---")
            for i, cmd in enumerate(command_chain):
                print(f"\nExecuting command {i+1}/{len(command_chain)}: '{cmd}'")
                if automator.execute_command(cmd):
                    print(f"Command {i+1} completed successfully.")
                else:
                    print(f"Command {i+1} failed or was aborted.")
                    # Decide whether to continue chain on failure - currently continues
                # Add a small delay between commands in the chain
                if i < len(command_chain) - 1:
                    print("Pausing briefly before next command...")
                    time.sleep(1.0) # 1 second delay
            print("\n--- Command Chain Execution Finished ---")

    # --- End Command Execution Logic ---

    clear_screen()
    print("\nExiting ES4 Companion.")
    os.system(f"title {original_title} - Exited")


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
