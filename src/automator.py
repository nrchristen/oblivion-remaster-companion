# Placeholder for window automation logic 

import win32gui
import win32api
import win32con
import win32process
import win32clipboard
import psutil
import time
import pywintypes
import logging
import os # Added for os.system/path
from datetime import datetime # Correct import for datetime.now()
import subprocess # Added for Popen

# Virtual key codes (consider moving to a constants file if grows)
VK_OEM_3 = 0xC0  # Backtick (`)
VK_RETURN = 0x0D # Enter
VK_CONTROL = 0x11 # Ctrl
VK_V = 0x56 # V key

class WindowAutomator:
    """Handles finding and interacting with the target game window."""

    def __init__(self, executable_name):
        self.executable_name = executable_name
        self.pid = None
        self.hwnd = None
        self.debug_mode = False # Flag for fallback mode
        self.debug_filepath = None # Path to the debug file
        logging.info(f"WindowAutomator initialized for executable: {self.executable_name}")

    def _press_key(self, key_code):
        """Simulates pressing and releasing a keyboard key."""
        try:
            win32api.keybd_event(key_code, 0, 0, 0) # Press
            time.sleep(0.03)
            win32api.keybd_event(key_code, 0, win32con.KEYEVENTF_KEYUP, 0) # Release
            time.sleep(0.03)
        except Exception as e:
            print(f"Error pressing key ({hex(key_code)}): {e}")

    def _paste_clipboard(self):
        """Simulates pressing Ctrl+V."""
        try:
            win32api.keybd_event(VK_CONTROL, 0, 0, 0) # Press Ctrl
            time.sleep(0.03)
            win32api.keybd_event(VK_V, 0, 0, 0)      # Press V
            time.sleep(0.03)
            win32api.keybd_event(VK_V, 0, win32con.KEYEVENTF_KEYUP, 0) # Release V
            time.sleep(0.03)
            win32api.keybd_event(VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0) # Release Ctrl
            time.sleep(0.03)
        except Exception as e:
            print(f"Error during paste simulation: {e}")

    def _set_clipboard_text(self, text):
        """Sets the Windows clipboard text."""
        # Don't interact with clipboard in debug mode
        if self.debug_mode:
            self._write_to_debug_file(f"[DEBUG] Skipped setting clipboard: {text}")
            return True # Simulate success for debug mode

        try:
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardText(text, win32clipboard.CF_UNICODETEXT)
            win32clipboard.CloseClipboard()
            return True
        except Exception as e:
            print(f"Error setting clipboard: {e}")
            try: # Attempt to close clipboard even if error occurred
                win32clipboard.CloseClipboard()
            except:
                pass
            return False

    def _find_hwnd_by_pid(self, target_pid):
        """Finds the main window handle (HWND) for a given process ID."""
        # This is an internal helper, shouldn't be affected by debug mode directly
        # print(f"  [*] Starting window enumeration for PID: {target_pid}") # Silenced
        found_hwnd = 0

        def enum_windows_callback(hwnd, lParam):
            nonlocal found_hwnd
            try:
                pid = None
                try:
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                except Exception:
                    return True # Continue enumeration if we can't get PID

                if pid == target_pid:
                    is_visible = False
                    try:
                        is_visible = win32gui.IsWindowVisible(hwnd)
                    except Exception:
                        return True # Continue on error

                    parent_hwnd = -1
                    try:
                        parent_hwnd = win32gui.GetParent(hwnd)
                    except Exception:
                        return True # Continue on error

                    if is_visible and parent_hwnd == 0:
                        window_title = "(Unknown)"
                        try:
                            window_title = win32gui.GetWindowText(hwnd)
                        except Exception:
                            pass
                        # print(f"    [*] Found potential main window: HWND={hwnd}, Title='{window_title}'") # Silenced
                        found_hwnd = hwnd
                        return False # Stop enumeration
            except Exception as e_callback:
                print(f"  [!] Unexpected error in enum_windows_callback for HWND {hwnd}: {e_callback}")
            return True # Continue enumeration

        try:
            win32gui.EnumWindows(enum_windows_callback, None)
        except pywintypes.error as e_enum:
            # print(f"  [!] pywintypes.error during EnumWindows: Code={e_enum.winerror}, Func='{e_enum.funcname}', Msg='{e_enum.strerror}'") # Silenced
            pass # Continue even if EnumWindows reports a (potentially spurious) error
        except Exception as e_enum_other:
            # print(f"  [!] Unexpected error calling EnumWindows: {e_enum_other}") # Silenced
            pass

        # print(f"  [*] Finished window enumeration. Found HWND: {found_hwnd}") # Silenced
        return found_hwnd

    def _write_to_debug_file(self, message):
        """Appends a message to the debug log file if active."""
        if not self.debug_mode or not self.debug_filepath:
            return # Do nothing if not in debug mode or file path is not set

        try:
            with open(self.debug_filepath, "a") as f:
                timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
                f.write(f"[{timestamp}] {message}\n")
        except Exception as e:
            # Log error writing to debug file, but don't crash the app
            logging.error(f"Error writing to debug file '{self.debug_filepath}': {e}")

    def find_process_and_window(self):
        """Finds the process ID and main window handle for the target executable.
           Enters debug file mode if the window is not found."""
        logging.info(f"Attempting to find process and window for {self.executable_name}...")
        self.pid = None
        self.hwnd = None
        # Reset debug mode at the start of each search
        self.debug_mode = False
        self.debug_filepath = None

        process_found = False
        try:
            for proc in psutil.process_iter(['pid', 'name']):
                if proc.info['name'] == self.executable_name:
                    self.pid = proc.info['pid']
                    logging.info(f"Found process {self.executable_name} with PID: {self.pid}")
                    process_found = True
                    break # Found the process

            if not process_found:
                logging.warning(f"Process {self.executable_name} not found.")
                # --- Enter Debug Mode --- 
                if not self.debug_mode:
                    self._enter_debug_mode()
                # ------------------------
                return False

            # Find window only if process was found
            hwnds = []
            win32gui.EnumWindows(enum_windows_callback_find_window, (self.pid, hwnds)) # Pass PID and list

            if hwnds:
                self.hwnd = hwnds[0] # Assume the first one found is the main window
                logging.info(f"Found main window for PID {self.pid} with HWND: {self.hwnd}")
                self.debug_mode = False # Corrected: Ensure debug_mode is off if found
                return True
            else:
                logging.warning(f"Process found (PID: {self.pid}), but no suitable window handle discovered.")
                self.pid = None # Reset pid if window not found
                # --- Enter Debug Mode --- 
                if not self.debug_mode:
                    self._enter_debug_mode()
                # ------------------------
                return False
        except psutil.NoSuchProcess:
            logging.warning(f"Process {self.executable_name} not found or disappeared during search (NoSuchProcess).")
            self.pid = None
            self.hwnd = None
            # --- Enter Debug Mode --- 
            if not self.debug_mode:
                self._enter_debug_mode()
            # ------------------------
            return False
        except Exception as e:
            logging.exception(f"Error finding process/window for {self.executable_name}: {e}")
            self.pid = None
            self.hwnd = None
            # --- Enter Debug Mode on other errors too? Yes. ---
            if not self.debug_mode:
                self._enter_debug_mode()
            # --------------------------------------------------
            return False

    def _check_hwnd(self, verbose=True):
        """Checks if the window handle is valid."""
        # Skip check in debug mode, as hwnd won't be valid
        if self.debug_mode:
             return True # Pretend it's valid for debug purposes

        if self.hwnd == 0 or self.hwnd is None: # Added None check
            if verbose:
                print("Error: Window handle not found.")
            return False
        return True

    def open_console(self, verbose=True):
        """Opens the game console or logs to debug file."""
        # --- Debug Mode Check ---
        if self.debug_mode:
            self._write_to_debug_file("[ACTION] Open Console (~) requested.")
            logging.info("Debug Mode: Logged 'open console' request.")
            return True # Simulate success
        # ------------------------

        # --- Always check for window before proceeding ---
        if not self.find_process_and_window():
            logging.error("Cannot open console: Game process/window not found.")
            if verbose: print("Error: Game not found. Cannot open console.")
            return False
        # -------------------------------------------------    
        
        logging.info(f"Attempting to open console (HWND: {self.hwnd})...")
        if not self.hwnd:
            logging.error("Cannot open console: Window handle (HWND) is invalid.")
            if verbose: print("Error: Invalid game window handle.")
            return False
        try:
            # Ensure window is in foreground (optional but often helps)
            try:
                win32gui.SetForegroundWindow(self.hwnd)
                time.sleep(0.1) # Small delay after setting foreground
            except Exception as e:
                logging.warning(f"Could not set game window to foreground (HWND: {self.hwnd}): {e}")
                # Continue anyway, might still work

            # Use keybd_event instead of PostMessage for console toggle
            tilde_key_code = 0xC0 # Hex value 192 for OEM_3 / Tilde key
            win32api.keybd_event(tilde_key_code, 0, 0, 0) # Press Down
            time.sleep(0.05)
            win32api.keybd_event(tilde_key_code, 0, win32con.KEYEVENTF_KEYUP, 0) # Press Up
            
            # Post key down and key up messages (OLD METHOD - OverflowError)
            # l_param_down = win32api.MAKELONG(0, win32api.MapVirtualKey(tilde_key_code, 0))
            # l_param_up = win32api.MAKELONG(0, win32api.MapVirtualKey(tilde_key_code, 0) | 0xC0000000)
            # win32api.PostMessage(self.hwnd, win32con.WM_KEYDOWN, tilde_key_code, l_param_down)
            # time.sleep(0.1) # Delay between down and up
            # win32api.PostMessage(self.hwnd, win32con.WM_KEYUP, tilde_key_code, l_param_up)
            
            logging.info(f"Sent console key press (keybd_event 0xC0) - Target HWND: {self.hwnd}")
            time.sleep(0.5) # Give console time to open
            return True
        except Exception as e:
            logging.exception(f"Error opening console (HWND: {self.hwnd}) using keybd_event")
            if verbose: print(f"Error sending console key press: {e}")
            return False

    def close_console(self, verbose=True):
        """Closes the game console or logs to debug file."""
         # --- Debug Mode Check ---
        if self.debug_mode:
            self._write_to_debug_file("[ACTION] Close Console (~) requested.")
            logging.info("Debug Mode: Logged 'close console' request.")
            return True # Simulate success
        # ------------------------

        logging.info(f"Attempting to close console (HWND: {self.hwnd})...")
        if not self.hwnd:
            logging.error("Cannot close console: Window handle (HWND) is invalid.")
            if verbose: print("Error: Invalid game window handle.")
            return False
            
        # Re-use the same key press logic as open_console
        try:
            # Use keybd_event instead of PostMessage
            tilde_key_code = 0xC0 # Hex value 192 for OEM_3 / Tilde key
            win32api.keybd_event(tilde_key_code, 0, 0, 0) # Press Down
            time.sleep(0.05)
            win32api.keybd_event(tilde_key_code, 0, win32con.KEYEVENTF_KEYUP, 0) # Press Up
            
            # Post key down and key up messages (OLD METHOD - OverflowError)
            # l_param_down = win32api.MAKELONG(0, win32api.MapVirtualKey(tilde_key_code, 0))
            # l_param_up = win32api.MAKELONG(0, win32api.MapVirtualKey(tilde_key_code, 0) | 0xC0000000)
            # win32api.PostMessage(self.hwnd, win32con.WM_KEYDOWN, tilde_key_code, l_param_down)
            # time.sleep(0.1)
            # win32api.PostMessage(self.hwnd, win32con.WM_KEYUP, tilde_key_code, l_param_up)
            
            logging.info(f"Sent console key press (keybd_event 0xC0) to close - Target HWND: {self.hwnd}")
            time.sleep(0.1) # Short delay after closing
            return True
        except Exception as e:
            logging.exception(f"Error closing console (HWND: {self.hwnd}) using keybd_event")
            if verbose: print(f"Error sending console key press: {e}")
            return False

    def execute_command_in_console(self, command, verbose=True):
        """Types a command into the console / logs to debug file."""
         # --- Debug Mode Check ---
        if self.debug_mode:
            self._write_to_debug_file(f"[EXECUTE] {command}")
            logging.info(f"Debug Mode: Logged command: {command}")
            return True # Simulate success
        # ------------------------

        logging.info(f"Executing in console (HWND: {self.hwnd}) using clipboard: \"{command}\"")
        if not self.hwnd:
            logging.error("Cannot execute in console: Window handle (HWND) is invalid.")
            if verbose: print("Error: Invalid game window handle.")
            return False
            
        try:
            # Set clipboard and paste
            logging.debug("Setting clipboard text...")
            if self._set_clipboard_text(command):
                logging.debug("Pasting from clipboard...")
                self._paste_clipboard()
                time.sleep(0.1) # Short delay after paste
            else:
                logging.error(f"Failed to set clipboard text for command: {command}")
                if verbose:
                    print("Error: Failed to set clipboard. Skipping command execution.")
                return False # Cannot proceed without clipboard

            # Press Enter (using keybd_event)
            logging.debug("Pressing Enter using keybd_event...")
            enter_key_code = win32con.VK_RETURN # Or 0x0D directly
            win32api.keybd_event(enter_key_code, 0, 0, 0) # Press Down
            time.sleep(0.05)
            win32api.keybd_event(enter_key_code, 0, win32con.KEYEVENTF_KEYUP, 0) # Press Up
            
            # Press Enter (OLD METHOD using PostMessage)
            # l_param_down = win32api.MAKELONG(0, win32api.MapVirtualKey(enter_key_code, 0))
            # l_param_up = win32api.MAKELONG(0, win32api.MapVirtualKey(enter_key_code, 0) | 0xC0000000)
            # win32api.PostMessage(self.hwnd, win32con.WM_KEYDOWN, enter_key_code, l_param_down)
            # time.sleep(0.05)
            # win32api.PostMessage(self.hwnd, win32con.WM_KEYUP, enter_key_code, l_param_up)
            
            logging.info(f"Pasted command and pressed Enter in console (HWND: {self.hwnd}) using keybd_event")
            time.sleep(0.5) # Give command time to execute
            return True
        except Exception as e:
            logging.exception(f"Error executing command '{command}' in console using clipboard (HWND: {self.hwnd})")
            if verbose: print(f"Error pasting command or pressing Enter: {e}")
            return False

    def execute_command(self, command, verbose=True):
        """Opens console, executes, closes OR logs sequence to debug file."""
        logging.info(f"Attempting full execution cycle for command: \"{command}\"")

        # --- Debug Mode Check (Initial State) ---
        if self.debug_mode:
            self._write_to_debug_file(f"[FULL CYCLE EXECUTE] {command}")
            logging.info(f"Debug Mode: Logged full cycle command (already in debug): {command}")
            # Return True because the action (logging) was successfully performed in debug mode.
            return True 
        # ------------------------

        # Note: open_console now performs the find_process_and_window check
        # and can enter debug mode itself.
        opened_successfully = self.open_console(verbose=verbose)

        # Check if debug mode was triggered *during* the open_console attempt
        if not opened_successfully and self.is_in_debug_mode():
             # Debug mode was just activated by open_console failing. Log the command that triggered it.
             self._write_to_debug_file(f"[FULL CYCLE EXECUTE - Triggered Debug] {command}")
             logging.warning(f"Debug Mode: Entered debug mode while attempting to execute '{command}'. Command logged.")
             # Even though logged, the *original intent* failed (opening console). Return False.
             return False # Return False because the primary action (opening the console) failed.

        # If console opened successfully (and we're not in debug mode)
        if opened_successfully:
            # The execute/close methods handle the debug check internally, but we shouldn't
            # reach here if open_console succeeded *while* in debug mode (it returns True early).
            # So we can assume we are NOT in debug mode here.
            if self.execute_command_in_console(command, verbose=verbose):
                if self.close_console(verbose=verbose):
                     # We already checked we're not in debug mode if opened_successfully was True.
                     logging.info(f"Full execution cycle successful for: \"{command}\"")
                     return True # Real success
                else:
                     # If close_console failed, it must have been a real attempt (not debug)
                    logging.error(f"Execution failed for '{command}': Could not close console.")
                    return False # Indicate cycle didn't complete cleanly
            else:
                # If execute failed, it must have been real (not debug)
                logging.error(f"Execution failed for '{command}': Could not execute in console.")
                self.close_console(verbose=False) # Attempt to close console anyway (handles debug mode internally, but shouldn't be in debug here)
                return False
        else:
             # If open_console failed and we *didn't* enter debug mode (unexpected, as find_process should set it)
             # Log the failure.
             logging.error(f"Execution failed for '{command}': Could not open console (and not in debug mode).")
             # Return False because the primary action (opening console) failed.
             return False

    def is_in_debug_mode(self):
        """Returns True if the automator is currently in debug file mode."""
        return self.debug_mode

    def get_debug_filepath(self):
        """Returns the path to the current debug file, or None."""
        return self.debug_filepath 

    def _enter_debug_mode(self):
        """Enters debug mode, creating a log file for commands."""
        logging.debug("Attempting to enter debug mode...") # Log entry
        try:
            # Use a fixed filename instead of timestamped
            fixed_filename = "debug_companion.txt"
            logging.debug(f"Debug filename set to: {fixed_filename}")
            self.debug_filepath = os.path.join(os.getcwd(), fixed_filename)
            logging.debug(f"Debug filepath set to: {self.debug_filepath}")
            self.debug_mode = True
            logging.debug("Set debug_mode = True")
            # Open in append mode
            logging.debug(f"Attempting to open {self.debug_filepath} for append...")
            with open(self.debug_filepath, "a", encoding='utf-8') as f:
                logging.debug(f"File {self.debug_filepath} opened successfully.")
                header = f"--- Debug Mode Entered: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---\n"
                f.write(header)
                logging.debug(f"Wrote header to {self.debug_filepath}")
            logging.info(f"Game window not found. Entering debug mode. Log file: {self.debug_filepath}")
            print(f"Companion: Game not found. Entering DEBUG mode. Commands will be written to {fixed_filename}")
            self._open_debug_log()
            logging.debug("Finished _enter_debug_mode successfully.")
            
        except Exception as e:
            logging.exception("Failed to enter debug mode or create log file.") # Keep existing exception log
            print(f"Companion: Error entering debug mode: {e}")
            self.debug_mode = False 
            self.debug_filepath = None

# Helper function for find_process_and_window (to avoid complex lambda)
def enum_windows_callback_find_window(hwnd, params):
    target_pid, hwnds_list = params
    if win32gui.IsWindowVisible(hwnd) and win32gui.IsWindowEnabled(hwnd):
        try:
            _, found_pid = win32process.GetWindowThreadProcessId(hwnd)
            if found_pid == target_pid:
                # Check if it's the main window (no parent or owner)
                if win32gui.GetParent(hwnd) == 0 and win32gui.GetWindow(hwnd, win32con.GW_OWNER) == 0:
                    hwnds_list.append(hwnd)
                    # return False # Stop enumeration once one is found?
                    # Or keep going? Let's just take the first one found.
        except Exception:
            pass # Ignore errors for specific windows (e.g. permissions)
    return True # Continue enumeration 