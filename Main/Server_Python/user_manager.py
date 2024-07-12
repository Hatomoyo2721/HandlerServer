import pathlib
import shutil
import json
import os
import socket
import sqlite3
import logging
from threading import Lock
from directory_manager import DirectoryManager
from file_manager import FileManager

class UserManager:
    USERS_DIR = pathlib.Path(os.path.dirname(os.path.abspath(__file__))) / 'users_directories'
    DB_PATH = pathlib.Path(os.path.dirname(os.path.abspath(__file__))) / 'users.db'

    def __init__(self, endpoint_manager):
        self.endpoint_manager = endpoint_manager
        self.lock = Lock()
        self._initialize_database()
        self._ensure_users_directory()
        
    def _initialize_database(self):
        with sqlite3.connect(self.DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    ip_address TEXT,
                    port INTEGER,
                    email TEXT,
                    password TEXT
                )
            ''')
            conn.commit()

    def _ensure_users_directory(self):
        self.USERS_DIR.mkdir(parents=True, exist_ok=True)   
    #=====================================================================================================================
    # Users Handle
    def add_user(self, s: socket.socket):
        try:
            raw_json = self.endpoint_manager.readUTF(s)
            if not raw_json:
                return
            
            json_obj = json.loads(raw_json)
            username = json_obj.get("username")
            if not username:
                return self.endpoint_manager.writeUTF(s, "ERROR: Missing argument")

            with self.lock:
                try:
                    with sqlite3.connect(self.DB_PATH) as conn:
                        cursor = conn.cursor()
                        cursor.execute('INSERT INTO users (username, ip_address, port, email, password) '
                                    'VALUES (?, ?, ?, ?, ?)',
                                    (username, json_obj.get("ipAddress", ""), json_obj.get("port", 0),
                                        json_obj.get("email", ""), json_obj.get("password", "")))
                        conn.commit()
                        
                    user_dir = self.USERS_DIR / username
                    user_dir.mkdir(parents=True, exist_ok=True)
                    self.endpoint_manager.writeUTF(s, "OK")
                except sqlite3.IntegrityError:
                    self.endpoint_manager.writeUTF(s, "ERROR: User already exists")
                except Exception as e:
                    logging.error(f"Error adding user: {e}\n")
                    self.endpoint_manager.writeUTF(s, f"ERROR: {e}")  
        except json.JSONDecodeError:
            logging.error("Error decoding JSON data from client")
            self.endpoint_manager.writeUTF(s, "ERROR: Invalid JSON format")
    #=====================================================================================================================
    #Directory User Handle
    def create_directory(self, s: socket.socket):
        directory_manager = DirectoryManager(self)
        directory_manager.create_directory(s)

    def load_directory(self, s: socket.socket):
        file_manager = FileManager(self)
        file_manager.load_directory(s)
