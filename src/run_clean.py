#!/usr/bin/env python3
"""
Clean Market Monitor Runner - No Emoji Spam
Runs your market monitor with minimal logging noise
"""

import os
import sys
import logging
import re
from io import StringIO

# Disable Azure Storage for local testing
os.environ['DISABLE_AZURE_STORAGE'] = 'true'


# Create custom logging handler that strips emojis
class CleanLogHandler(logging.StreamHandler):
    def emit(self, record):
        try:
            # Strip emojis from log messages
            if hasattr(record, 'msg'):
                record.msg = re.sub(r'[^\x00-\x7F]+', '', str(record.msg))
            if hasattr(record, 'args') and record.args:
                clean_args = []
                for arg in record.args:
                    if isinstance(arg, str):
                        clean_args.append(re.sub(r'[^\x00-\x7F]+', '', arg))
                    else:
                        clean_args.append(arg)
                record.args = tuple(clean_args)
            super().emit(record)
        except UnicodeEncodeError:
            # If still failing, just skip this log entry
            pass


# Configure clean logging
def setup_clean_logging():
    # Remove all existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Add our clean handler
    clean_handler = CleanLogHandler()
    clean_handler.setLevel(logging.WARNING)  # Only show warnings and errors
    formatter = logging.Formatter('%(levelname)s - %(message)s')
    clean_handler.setFormatter(formatter)
    root_logger.addHandler(clean_handler)
    root_logger.setLevel(logging.WARNING)


def main():
    print("Running Bitcoin Market Monitor (Clean Mode)")
    print("=" * 50)

    # Setup clean logging
    setup_clean_logging()

    # Import and run your monitor
    try:
        from manual_market_monitor import ManualMarketMonitor

        monitor = ManualMarketMonitor()
        success = monitor.run_market_analysis()

        if success:
            print("\nSUCCESS: Market analysis completed and email sent!")
        else:
            print("\nPARTIAL SUCCESS: Analysis completed but report not sent")

    except Exception as e:
        print(f"\nERROR: {e}")
        return False

    return True


if __name__ == "__main__":
    main()
