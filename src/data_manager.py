#!/usr/bin/env python3
"""
Data Manager - Safe JSON Operations for MSTR Data
Handles BTC holdings data and message system with file locking
"""

import json
import os
import logging
import fcntl
import time
from datetime import datetime
from typing import Dict, Optional, Any
from contextlib import contextmanager


class DataManager:
    """Safe JSON file operations for MSTR data with file locking"""

    def __init__(self, data_file_path: str = "mstr_json_data/mstr_data.json"):
        self.data_file_path = data_file_path
        self.data_dir = os.path.dirname(data_file_path)
        self._ensure_data_directory()

    def _ensure_data_directory(self):
        """Create data directory if it doesn't exist"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            logging.info(f"Created data directory: {self.data_dir}")

    @contextmanager
    def _file_lock(self, file_handle, operation):
        """Context manager for file locking"""
        try:
            fcntl.flock(file_handle.fileno(), operation)
            yield
        finally:
            fcntl.flock(file_handle.fileno(), fcntl.LOCK_UN)

    def load_data(self) -> Dict[str, Any]:
        """
        Safely load JSON data with file locking

        Returns:
            Dict with 'btc_data' and 'messages' keys, or default structure if file doesn't exist
        """
        default_data = {
            "btc_data": {},
            "messages": {}
        }

        if not os.path.exists(self.data_file_path):
            logging.info(f"Data file not found: {self.data_file_path}, returning default structure")
            return default_data

        try:
            with open(self.data_file_path, 'r', encoding='utf-8') as f:
                with self._file_lock(f, fcntl.LOCK_SH):  # Shared lock for reading
                    data = json.load(f)

            # Validate structure
            if not isinstance(data, dict):
                logging.warning("Invalid data structure, returning default")
                return default_data

            # Ensure required keys exist
            if 'btc_data' not in data:
                data['btc_data'] = {}
            if 'messages' not in data:
                data['messages'] = {}

            logging.info(f"Loaded data: {len(data['btc_data'])} BTC entries, {len(data['messages'])} messages")
            return data

        except json.JSONDecodeError as e:
            logging.error(f"JSON parse error in {self.data_file_path}: {str(e)}")
            return default_data
        except Exception as e:
            logging.error(f"Error loading data file: {str(e)}")
            return default_data

    def save_data(self, data: Dict[str, Any]) -> bool:
        """
        Safely save JSON data with file locking and atomic write

        Args:
            data: Dictionary with 'btc_data' and 'messages' keys

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Validate data structure
            if not isinstance(data, dict):
                logging.error("Invalid data structure for saving")
                return False

            if 'btc_data' not in data or 'messages' not in data:
                logging.error("Missing required keys in data structure")
                return False

            # Atomic write using temporary file
            temp_file_path = f"{self.data_file_path}.tmp"

            with open(temp_file_path, 'w', encoding='utf-8') as f:
                with self._file_lock(f, fcntl.LOCK_EX):  # Exclusive lock for writing
                    json.dump(data, f, indent=2, ensure_ascii=False)

            # Atomic move
            os.replace(temp_file_path, self.data_file_path)

            logging.info(f"Saved data: {len(data['btc_data'])} BTC entries, {len(data['messages'])} messages")
            return True

        except Exception as e:
            logging.error(f"Error saving data file: {str(e)}")
            # Clean up temp file if it exists
            if os.path.exists(f"{self.data_file_path}.tmp"):
                try:
                    os.remove(f"{self.data_file_path}.tmp")
                except:
                    pass
            return False

    def get_btc_holdings_data(self) -> Dict[str, Dict[str, int]]:
        """
        Get BTC holdings data

        Returns:
            Dict with date keys and BTC holdings: {"2025-07-21": {"btc": 607770}}
        """
        data = self.load_data()
        return data.get('btc_data', {})

    def get_latest_undisplayed_message(self) -> Optional[Dict[str, Any]]:
        """
        Get the latest undisplayed message by date

        Returns:
            Dict with 'date', 'content', 'displayed' keys, or None if no undisplayed messages
        """
        data = self.load_data()
        messages = data.get('messages', {})

        # Find undisplayed messages
        undisplayed = {
            date: msg for date, msg in messages.items()
            if not msg.get('displayed', False)
        }

        if not undisplayed:
            logging.info("No undisplayed messages found")
            return None

        # Get latest by date
        latest_date = max(undisplayed.keys())
        latest_message = undisplayed[latest_date]

        result = {
            'date': latest_date,
            'content': latest_message.get('content', ''),
            'displayed': latest_message.get('displayed', False)
        }

        logging.info(f"Found latest undisplayed message from {latest_date}")
        return result

    def mark_message_displayed(self, message_date: str) -> bool:
        """
        Mark a message as displayed

        Args:
            message_date: Date key of the message to mark as displayed

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            data = self.load_data()

            if message_date not in data.get('messages', {}):
                logging.warning(f"Message date {message_date} not found")
                return False

            data['messages'][message_date]['displayed'] = True

            success = self.save_data(data)
            if success:
                logging.info(f"Marked message {message_date} as displayed")
            else:
                logging.error(f"Failed to save message display status for {message_date}")

            return success

        except Exception as e:
            logging.error(f"Error marking message as displayed: {str(e)}")
            return False

    def add_btc_holdings(self, date: str, btc_amount: int) -> bool:
        """
        Add BTC holdings data for a specific date

        Args:
            date: Date in YYYY-MM-DD format
            btc_amount: BTC holdings amount

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            data = self.load_data()

            if 'btc_data' not in data:
                data['btc_data'] = {}

            data['btc_data'][date] = {'btc': btc_amount}

            success = self.save_data(data)
            if success:
                logging.info(f"Added BTC holdings: {date} -> {btc_amount}")
            else:
                logging.error(f"Failed to save BTC holdings for {date}")

            return success

        except Exception as e:
            logging.error(f"Error adding BTC holdings: {str(e)}")
            return False

    def add_message(self, date: str, content: str, displayed: bool = False) -> bool:
        """
        Add a message

        Args:
            date: Date in YYYY-MM-DD format
            content: Message content
            displayed: Whether message has been displayed

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            data = self.load_data()

            if 'messages' not in data:
                data['messages'] = {}

            data['messages'][date] = {
                'content': content,
                'displayed': displayed
            }

            success = self.save_data(data)
            if success:
                logging.info(f"Added message: {date}")
            else:
                logging.error(f"Failed to save message for {date}")

            return success

        except Exception as e:
            logging.error(f"Error adding message: {str(e)}")
            return False

    def get_data_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the data

        Returns:
            Dict with statistics about BTC data and messages
        """
        try:
            data = self.load_data()
            btc_data = data.get('btc_data', {})
            messages = data.get('messages', {})

            # BTC data stats
            btc_dates = list(btc_data.keys())
            btc_dates.sort()

            # Message stats
            undisplayed_count = sum(1 for msg in messages.values() if not msg.get('displayed', False))

            stats = {
                'btc_data': {
                    'total_entries': len(btc_data),
                    'earliest_date': btc_dates[0] if btc_dates else None,
                    'latest_date': btc_dates[-1] if btc_dates else None
                },
                'messages': {
                    'total_messages': len(messages),
                    'undisplayed_count': undisplayed_count,
                    'displayed_count': len(messages) - undisplayed_count
                }
            }

            return stats

        except Exception as e:
            logging.error(f"Error getting data stats: {str(e)}")
            return {'error': str(e)}
