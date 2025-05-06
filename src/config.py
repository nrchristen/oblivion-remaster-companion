import logging
import sys
import os

LOG_FILE = 'companion_log.txt'

def setup_logging():
    """Configures file and console logging."""
    log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s:%(lineno)d - %(message)s')
    logger = logging.getLogger() # Get the root logger
    logger.setLevel(logging.DEBUG) # Set the lowest level for the logger

    # Clear existing handlers (important if this runs multiple times or other libs configure logging)
    if logger.hasHandlers():
        logger.handlers.clear()

    # File Handler (always log DEBUG level to file)
    try:
        # Ensure the log directory exists (assuming logs go in the main app directory for simplicity)
        # For packaged apps, consider using platform-specific app data dirs.
        log_dir = os.path.dirname(LOG_FILE)
        if log_dir and not os.path.exists(log_dir): # Check if log_dir is not empty
             os.makedirs(log_dir, exist_ok=True)
             
        file_handler = logging.FileHandler(LOG_FILE, mode='w', encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(log_formatter)
        logger.addHandler(file_handler)
        # Use print here as logging might not be fully configured when this runs
        print(f"--- File logging configured ({LOG_FILE}) ---") 
    except Exception as log_setup_e:
        # If file logging fails, we can't log to file, print critical error
        print(f"FATAL: Could not set up file logging to {LOG_FILE}: {log_setup_e}")
        # Depending on severity, you might exit or just continue without file logging
        # exit(1)

    # Optional: Console Handler (show INFO level to console when running)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO) # Show INFO and above in console
    console_handler.setFormatter(log_formatter)
    logger.addHandler(console_handler)
    print("--- Console logging configured ---") 