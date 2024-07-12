import pathlib
import shutil
import json
import os
import socket
import sqlite3
from threading import Lock

class UserManager:
    BASE_DIR = pathlib.Path(os.path.dirname(os.path.abspath(__file__))) / 'users_directories'

    def __init__(self, endpoint_manager):
        self.user_infos = {}
        self.lock = Lock()
        self.endpoint_manager = endpoint_manager
        self.db_path = self.BASE_DIR / 'users.db'
        self._initialize_database()
        
    def _initialize_database(self):
        with sqlite3.connect(self.db_path) as conn:
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
            
    #=====================================================================================================================
    
    # Users Handle

    def add_user(self, s: socket.socket):
        """
        Add a new user to the user_infos.json and users.db dictionary.
        """
        # Read the JSON data from the socket
        raw_json = self.endpoint_manager.readUTF(s)
        if not raw_json:
            return

        # Parse the JSON data into a dictionary
        json_obj = json.loads(raw_json)
        username = json_obj.pop("username", None)
        
        if not username:
            return self.endpoint_manager.writeUTF(s, "ERROR: Missing argument")

        user_info = json.dumps(json_obj)
        
        with self.lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute('INSERT INTO users (username, ip_address, port, email, password) '
                                   'VALUES (?, ?, ?, ?, ?)',
                                   (username, json_obj.get("ipAddress", ""), json_obj.get("port", 0),
                                    json_obj.get("email", ""), json_obj.get("password", "")))
                    conn.commit()
                    
                user_dir = self.BASE_DIR / username
                user_dir.mkdir(parents=True, exist_ok=True)
                self.endpoint_manager.writeUTF(s, "OK")
            except sqlite3.IntegrityError:
                self.endpoint_manager.writeUTF(s, "ERROR: User already exists")
            except Exception as e:
                print(f"Error adding user: {e}")
                self.endpoint_manager.writeUTF(s, f"ERROR: {e}")
                
    def delete_user(self, username):
        """
        Delete a user from the database and JSON file.
        """
        with self.lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute('DELETE FROM users WHERE username = ?', (username,))
                    conn.commit()

                user_dir = self.BASE_DIR / username
                if user_dir.exists():
                    shutil.rmtree(user_dir)

                return True
            except Exception as e:
                print(f"Error deleting user: {e}")
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
            return EndpointManager.writeUTF(s, "ERROR: Missing username") # type: ignore
        filename = self.endpoint_manager.readUTF(s)
        if not filename:
            return self.endpoint_manager.writeUTF(s, "ERROR: Missing filename")

        user = user.decode()
        filename = filename.decode()
        print(user)
        print(filename)

        with self.lock:
            try:
                # Create the user's directory in the base directory
                user_dir = self.BASE_DIR / user
                user_dir.mkdir(parents=True, exist_ok=True)

                # Copy the file to the user's directory
                shutil.copyfile(filename, user_dir / pathlib.Path(filename).name)

                print(f"File {filename} copied to {user_dir / pathlib.Path(filename).name}")

                self.endpoint_manager.writeUTF(s, "OK")
            except Exception as e:
                print(f"Error copying file: {e}")
                self.endpoint_manager.writeUTF(s, f"ERROR: {e}")
                
    #=====================================================================================================================
    
    #Directory User Handle
    
    def create_directory(self, s: socket.socket):
        username = self.endpoint_manager.readUTF(s)
        if not username:
            return self.endpoint_manager.writeUTF(s, "ERROR: Missing username")
        
        username = username.decode()
        user_dir = self.BASE_DIR / "users_directories" / username
        try:
            user_dir.mkdir(parents=True, exist_ok=True)
            self.endpoint_manager.writeUTF(s, "OK")
        except FileExistsError:
            self.endpoint_manager.writeUTF(s, "ERROR: Directory already exists")
        except Exception as e:
            print(f"Error creating directory: {e}")
            self.endpoint_manager.writeUTF(s, f"ERROR: {e}")

    def list_directory(self, s: socket.socket):
        username = self.endpoint_manager.readUTF(s)
        if not username:
            return self.endpoint_manager.writeUTF(s, "ERROR: Missing username")
        
        username = username.decode()
        user_dir = self.BASE_DIR / username
        try:
            if user_dir.exists():
                files = [str(f) for f in user_dir.iterdir()]
                self.endpoint_manager.writeUTF(s, json.dumps(files))
            else:
                self.endpoint_manager.writeUTF(s, "ERROR: Directory not found")
        except Exception as e:
            print(f"Error listing directory: {e}")
            self.endpoint_manager.writeUTF(s, f"ERROR: {e}")