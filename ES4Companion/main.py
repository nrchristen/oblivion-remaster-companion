import sys
import os

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

def run_companion():
    """Main function to run the ES4 Companion tool."""
    original_title = "ES4Companion" # Store original title (optional)
    os.system(f"title {original_title}") # Set initial title
    clear_screen() # Clear screen initially
    print(SWORD_ART) # Added ASCII art print
    print("--- Elder Scrolls IV: Oblivion Companion ---")
    print("Initializing...")

    # Initialize the window automator
    automator = WindowAutomator(TARGET_EXECUTABLE)

    # Find the game process and window *first*
    # If the game isn't running, no point asking the user for commands
    if not automator.find_process_and_window():
        print("\nFailed to find running game process or window.")
        print("Please ensure the game is running and try again.")
        input("Press Enter to exit.") # Keep console open
        return

    # --- Window Found - Update Title --- Added
    active_title = "ES4Companion - Active (Connected to Game)"
    os.system(f"title {active_title}")
    # --- End Added ---

    print("\nGame window located successfully.")

    # Main loop to get and execute commands
    while True:
        command_string = get_command_from_user() # Get command via UI module

        if command_string is None: # User chose to exit
            break

        # Execute the command
        print("\nAttempting to execute command...")
        if automator.execute_command(command_string):
            print("Command sequence completed successfully.")
        else:
            print("Command sequence failed or was aborted.")

        print("\n----------------------------------------")
        # Loop continues automatically back to the main menu
        # clear_screen() # Screen is cleared at the start of get_command_from_user loop
        # another = input("Run another command? (y/n): ").strip().lower()
        # if another != 'y':
        #     break

    clear_screen() # Clear screen before final exit message
    print("\nExiting ES4 Companion.")
    os.system(f"title {original_title} - Exited") # Reset title on exit


if __name__ == "__main__":
    # It's generally recommended to run scripts interacting with other windows
    # with admin privileges if the target window might be elevated.
    print("INFO: Ensure this script is run with administrator privileges if the game requires them.")
    run_companion()
    input("Press Enter to close the console window.") # Keep console open
