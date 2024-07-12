import logging
import pathlib
import socket


class DirectoryManager:
    USERS_DIR = pathlib.Path(__file__).resolve().parent / 'users_directories'

    def __init__(self, user_manager):
        self.user_manager = user_manager

    def create_directory(self, s: socket.socket):
        try:
            username = self.user_manager.endpoint_manager.readUTF(s)
            if not username:
                return self.user_manager.endpoint_manager.writeUTF(s, "ERROR: Missing username")

            user_dir = self.USERS_DIR / username
            try:
                user_dir.mkdir(parents=True, exist_ok=True)
                self.user_manager.endpoint_manager.writeUTF(s, "OK")
            except FileExistsError:
                self.user_manager.endpoint_manager.writeUTF(s, "ERROR: Directory already exists")
            except Exception as e:
                logging.error(f"Error creating directory: {e}")
                self.user_manager.endpoint_manager.writeUTF(s, f"ERROR: {e}")
        except Exception as e:
            logging.error(f"Error handling create_directory request: {e}")
            self.user_manager.endpoint_manager.writeUTF(s, f"ERROR: {e}")