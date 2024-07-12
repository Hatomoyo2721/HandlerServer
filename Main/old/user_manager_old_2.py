from hashlib import sha256
import hashlib
import pathlib
import shutil
import json
import os
import socket
import sqlite3
import logging
from threading import Lock

class UserManager:
    USERS_DIR = pathlib.Path(os.path.dirname(os.path.abspath(__file__))) / 'users_directories'
    DB_PATH = pathlib.Path(os.path.dirname(os.path.abspath(__file__))) / 'users.db'
    DB_PATH_PLAINTEXT = pathlib.Path(os.path.dirname(os.path.abspath(__file__))) / 'users_plaintext.db'

    def __init__(self, endpoint_manager, manager_key):
        self.endpoint_manager = endpoint_manager
        self.lock = Lock()
        self.manager_key = hashlib.sha256(manager_key.encode('utf-8')).hexdigest()
        self._initialize_databases()
        self._ensure_users_directory()
        
    def _initialize_databases(self):
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

        with sqlite3.connect(self.DB_PATH_PLAINTEXT) as conn_plaintext:
            cursor_plaintext = conn_plaintext.cursor()
            cursor_plaintext.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    ip_address TEXT,
                    port INTEGER,
                    email TEXT,
                    password TEXT
                )
            ''')
            conn_plaintext.commit()
    #============================================================

    def _ensure_users_directory(self):
        self.USERS_DIR.mkdir(parents=True, exist_ok=True)
        
    def hash_password(self, password):
        return sha256(password.encode('utf-8')).hexdigest()

    #============================================================
    # Users Handle
    def add_user(self, s: socket.socket):
        """
        Add a new user to the users.db with encrypted password.
        """
        raw_json = self.endpoint_manager.readUTF(s)
        if not raw_json:
            return
        json_obj = json.loads(raw_json)
        username = json_obj.pop("username", None)
        if not username:
            return self.endpoint_manager.writeUTF(s, "ERROR: Missing argument")

        password = self.hash_password(json_obj.get("password", ""))
        
        with self.lock:
            try:
                with sqlite3.connect(self.DB_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute('INSERT INTO users (username, ip_address, port, email, password) '
                                   'VALUES (?, ?, ?, ?, ?)',
                                   (username, json_obj.get("ipAddress", ""), json_obj.get("port", 0),
                                    json_obj.get("email", ""), password))
                    conn.commit()
                    
                user_dir = self.USERS_DIR / username
                user_dir.mkdir(parents=True, exist_ok=True)
                self.endpoint_manager.writeUTF(s, "OK")
            except sqlite3.IntegrityError:
                self.endpoint_manager.writeUTF(s, "ERROR: User already exists")
            except Exception as e:
                logging.error(f"Error adding user: {e}")
                self.endpoint_manager.writeUTF(s, f"ERROR: {e}")
                
    def add_user_plaintext(self, s: socket.socket, manager_key):
        """
        Add a new user to the users_plaintext.db with plaintext password, requires manager key.
        """
        if manager_key != self.manager_key:
            return self.endpoint_manager.writeUTF(s, "ERROR: Unauthorized access")

        raw_json = self.endpoint_manager.readUTF(s)
        if not raw_json:
            return
        json_obj = json.loads(raw_json)
        username = json_obj.pop("username", None)
        if not username:
            return self.endpoint_manager.writeUTF(s, "ERROR: Missing argument")

        password = json_obj.get("password", "")  # Assuming password is provided in plaintext
        
        with self.lock:
            try:
                with sqlite3.connect(self.DB_PATH_PLAINTEXT) as conn_plaintext:
                    cursor_plaintext = conn_plaintext.cursor()
                    cursor_plaintext.execute('INSERT INTO users (username, ip_address, port, email, password) '
                                            'VALUES (?, ?, ?, ?, ?)',
                                            (username, json_obj.get("ipAddress", ""), json_obj.get("port", 0),
                                            json_obj.get("email", ""), password))
                    conn_plaintext.commit()

                user_dir = self.USERS_DIR / username
                user_dir.mkdir(parents=True, exist_ok=True)
                self.endpoint_manager.writeUTF(s, "OK")
            except sqlite3.IntegrityError:
                self.endpoint_manager.writeUTF(s, "ERROR: User already exists")
            except Exception as e:
                logging.error(f"Error adding user: {e}")
                self.endpoint_manager.writeUTF(s, f"ERROR: {e}")

    def delete_user(self, username):
        """
        Delete a user from both databases and delete user directory.
        """
        with self.lock:
            try:
                with sqlite3.connect(self.DB_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute('DELETE FROM users WHERE username = ?', (username,))
                    conn.commit()

                with sqlite3.connect(self.DB_PATH_PLAINTEXT) as conn_plaintext:
                    cursor_plaintext = conn_plaintext.cursor()
                    cursor_plaintext.execute('DELETE FROM users WHERE username = ?', (username,))
                    conn_plaintext.commit()

                user_dir = self.USERS_DIR / username
                if user_dir.exists():
                    shutil.rmtree(user_dir)

                return True
            except Exception as e:
                logging.error(f"Error deleting user: {e}")
                return False
            
    def upload(self, s: socket.socket):
        """
        Uploads a file to the user's directory.

        The file is copied to the user's directory in the project's base directory.

        Args:
            s (socket.socket): The socket object representing the connection to the client.

        Returns:
            str: The response message indicating the success or failure of the upload.

        """
        user = self.endpoint_manager.readUTF(s)
        if not user:
            return self.endpoint_manager.writeUTF(s, "ERROR: Missing username")
        
        filename = self.endpoint_manager.readUTF(s)
        if not filename:
            return self.endpoint_manager.writeUTF(s, "ERROR: Missing filename")

        user_dir = self.USERS_DIR / user
        with self.lock:
            try:
                user_dir.mkdir(parents=True, exist_ok=True)
                file_path = user_dir / pathlib.Path(filename).name
                with open(file_path, 'wb') as f:
                    while True:
                        data = s.recv(1024)
                        if not data:
                            break
                        f.write(data)
                self.endpoint_manager.writeUTF(s, "OK")
            except Exception as e:
                logging.error(f"Error uploading file: {e}\n")
                self.endpoint_manager.writeUTF(s, f"ERROR: {e}")
                
    #============================================================
    #Directory User Handle
    def create_directory(self, s: socket.socket):
        """
        Create a directory for the specified user.
        """
        username = self.endpoint_manager.readUTF(s)
        if not username:
            return self.endpoint_manager.writeUTF(s, "ERROR: Missing username")
        
        user_dir = self.USERS_DIR / username
        try:
            user_dir.mkdir(parents=True, exist_ok=True)
            self.endpoint_manager.writeUTF(s, "OK")
        except FileExistsError:
            self.endpoint_manager.writeUTF(s, "ERROR: Directory already exists")
        except Exception as e:
            logging.error(f"Error creating directory: {e}")
            self.endpoint_manager.writeUTF(s, f"ERROR: {e}")
            
    def load_directory(self, s: socket.socket):
        """
        Load the list of files in the user's directory.
        """
        username = self.endpoint_manager.readUTF(s)
        if not username:
            return self.endpoint_manager.writeUTF(s, "ERROR: Missing username")
        
        user_dir = self.USERS_DIR / username
        try:
            if user_dir.exists():
                files = [f.name for f in user_dir.iterdir() if f.is_file()]
                self.endpoint_manager.writeUTF(s, json.dumps(files))
            else:
                self.endpoint_manager.writeUTF(s, "ERROR: Directory not found")
        except Exception as e:  
            logging.error(f"Error loading directory: {e}\n")
            self.endpoint_manager.writeUTF(s, f"ERROR: {e}")

    def authenticate_manager(self, s: socket.socket, manager_key):
        """
        Authenticate the manager using the provided key.
        """
        if manager_key == self.manager_key:
            self.endpoint_manager.writeUTF(s, "OK")
        else:
            self.endpoint_manager.writeUTF(s, "ERROR: Authentication failed")
