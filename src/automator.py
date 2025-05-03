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

    def find_process_and_window(self):
        """Finds the process ID and main window handle for the target executable."""
        logging.info(f"Attempting to find process and window for {self.executable_name}...")
        self.pid = None
        self.hwnd = None
        try:
            for proc in psutil.process_iter(['pid', 'name']):
                if proc.info['name'] == self.executable_name:
                    self.pid = proc.info['pid']
                    logging.info(f"Found process {self.executable_name} with PID: {self.pid}")
                    break # Found the process

            if not self.pid:
                logging.warning(f"Process {self.executable_name} not found.")
                return False

            def enum_windows_callback(hwnd, hwnds):
                if win32gui.IsWindowVisible(hwnd) and win32gui.IsWindowEnabled(hwnd):
                    _, found_pid = win32process.GetWindowThreadProcessId(hwnd)
                    if found_pid == self.pid:
                        # Check if it's the main window (no parent or owner)
                        # This heuristic might need adjustment for specific games
                        if win32gui.GetParent(hwnd) == 0 and win32gui.GetWindow(hwnd, win32con.GW_OWNER) == 0:
                            hwnds.append(hwnd)
                return True # Continue enumeration

            hwnds = []
            win32gui.EnumWindows(enum_windows_callback, hwnds)

            if hwnds:
                self.hwnd = hwnds[0] # Assume the first one found is the main window
                logging.info(f"Found main window for PID {self.pid} with HWND: {self.hwnd}")
                return True
            else:
                logging.warning(f"Process found (PID: {self.pid}), but no suitable window handle discovered.")
                self.pid = None # Reset pid if window not found
                return False
        except psutil.NoSuchProcess:
            logging.warning(f"Process {self.executable_name} disappeared during search.")
            self.pid = None
            self.hwnd = None
            return False
        except Exception as e:
            logging.exception(f"Error finding process/window for {self.executable_name}")
            self.pid = None
            self.hwnd = None
            return False

    def _check_hwnd(self, verbose=True):
        """Checks if the window handle is valid."""
        if self.hwnd == 0:
            if verbose:
                print("Error: Window handle not found.")
            return False
        return True

    def open_console(self, verbose=True):
        """Opens the game console by sending the appropriate key press."""
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
        """Closes the game console by sending the ` key press again."""
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
        """Types a command into the (already open) console using clipboard paste and presses Enter."""
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
        """Opens console, executes a single command, and closes console."""
        logging.info(f"Attempting full execution cycle for command: \"{command}\"")
        # --- Check game status FIRST --- 
        # No need to call find_process_and_window directly, open_console does it.
        # if not self.find_process_and_window():
        #     logging.error(f"Cannot execute command '{command}': Game not found.")
        #     if verbose: print("Error: Game not found. Cannot execute command.")
        #     return False
        # --------------------------------
        
        # Note: open_console now performs the find_process_and_window check
        if self.open_console(verbose=verbose):
            if self.execute_command_in_console(command, verbose=verbose):
                if self.close_console(verbose=verbose):
                    logging.info(f"Full execution cycle successful for: \"{command}\"")
                    return True
                else:
                    logging.error(f"Execution failed for '{command}': Could not close console.")
                    # Console might be left open, but command likely executed
                    return False # Indicate cycle didn't complete cleanly
            else:
                logging.error(f"Execution failed for '{command}': Could not execute in console.")
                self.close_console(verbose=False) # Attempt to close console anyway
                return False
        else:
            logging.error(f"Execution failed for '{command}': Could not open console.")
            # If open failed, find_process_and_window likely failed within it.
            return False 