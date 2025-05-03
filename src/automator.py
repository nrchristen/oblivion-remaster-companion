# Placeholder for window automation logic 

import win32gui
import win32api
import win32con
import win32process
import win32clipboard
import psutil
import time
import pywintypes

# Virtual key codes (consider moving to a constants file if grows)
VK_OEM_3 = 0xC0  # Backtick (`)
VK_RETURN = 0x0D # Enter
VK_CONTROL = 0x11 # Ctrl
VK_V = 0x56 # V key

class WindowAutomator:
    """Handles finding and interacting with the target game window."""

    def __init__(self, target_executable_name):
        self.target_exe = target_executable_name
        self.hwnd = 0

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
        """Finds the target process and its main window HWND."""
        print(f"Looking for process: '{self.target_exe}'")
        found_pid = None
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if proc.info['name'] and proc.info['name'].lower() == self.target_exe.lower():
                    found_pid = proc.info['pid']
                    # print(f"Process found (PID: {found_pid}).") # Silenced
                    break
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

        if not found_pid:
            print(f"Error: Process '{self.target_exe}' not found.")
            return False

        # print(f"Finding window for PID: {found_pid}") # Silenced
        self.hwnd = self._find_hwnd_by_pid(found_pid)

        if self.hwnd == 0:
            print(f"Error: Could not find main window for PID {found_pid}.")
            return False

        # print(f"Window found (HWND: {self.hwnd}).") # Silenced - main.py reports success
        return True

    def _check_hwnd(self, verbose=True):
        """Checks if the window handle is valid."""
        if self.hwnd == 0:
            if verbose:
                print("Error: Window handle not found.")
            return False
        return True

    def open_console(self, verbose=True):
        """Brings window to front and opens the console."""
        if not self._check_hwnd(verbose):
            return False
        try:
            if verbose:
                print("Bringing window to front...")
            win32gui.SetForegroundWindow(self.hwnd)
            time.sleep(0.25) # Wait for window to activate

            if verbose:
                print("Opening console ('`')...")
            self._press_key(VK_OEM_3)
            time.sleep(0.15) # Wait slightly longer for console to open fully
            return True
        except Exception as e:
            if verbose:
                print(f"Error opening console: {e}")
            return False

    def close_console(self, verbose=True):
        """Closes the console."""
        # No HWND check needed here, just send the key press
        try:
            if verbose:
                print("Closing console ('`')...")
            self._press_key(VK_OEM_3)
            time.sleep(0.05) # Small delay after closing
            return True
        except Exception as e:
            if verbose:
                print(f"Error closing console: {e}")
            return False

    def execute_command_in_console(self, command_string, verbose=True):
        """Executes a command assuming the console is already open."""
        if not self._check_hwnd(verbose):
             return False
        # Assumes window is focused and console is open
        try:
            if verbose:
                print(f"  Executing: '{command_string}'") # Indented for clarity within sequence

            # Set clipboard and paste
            if verbose:
                print("    Setting clipboard and pasting...") # Indented
            if self._set_clipboard_text(command_string):
                self._paste_clipboard()
                time.sleep(0.1)
            else:
                if verbose:
                    print("    Failed to set clipboard. Skipping command execution.") # Indented
                return False # Cannot proceed without clipboard

            # Execute command
            if verbose:
                print("    Pressing Enter...") # Indented
            self._press_key(VK_RETURN)
            time.sleep(0.15) # Give a bit more time for command to register/start
            return True
        except Exception as e:
            if verbose:
                 print(f"    Error executing command '{command_string}' in console: {e}") # Indented
            return False

    def execute_single_command(self, command_string, verbose=True):
         """Opens console, executes a single command, and closes console."""
         # This keeps the original full cycle logic for single commands
         if not self._check_hwnd(verbose): return False

         if verbose:
             print(f"Executing single command cycle: '{command_string}'")

         opened = self.open_console(verbose)
         executed = False
         if opened:
             # Use the new method assuming console is open
             executed = self.execute_command_in_console(command_string, verbose)
         
         # Always try to close if opened, even if execution failed
         closed = False
         if opened:
             closed = self.close_console(verbose)

         if verbose:
             print("Single command cycle finished.")

         # Return True only if open, execute, and close were successful
         return opened and executed and closed

    # Keep execute_command as an alias for the full cycle method
    def execute_command(self, command_string, verbose=True):
        """Alias for execute_single_command for backward compatibility / single use case."""
        return self.execute_single_command(command_string, verbose=verbose) 