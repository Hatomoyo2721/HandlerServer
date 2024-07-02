import pathlib
import shutil
import json
import os
import socket
from threading import Lock

class UserManager:
    BASE_DIR = pathlib.Path(os.path.dirname(os.path.abspath(__file__)))

    def __init__(self, endpoint_manager):
        self.user_infos = {}
        self.lock = Lock()
        self.endpoint_manager = endpoint_manager

    def add_user(self, s: socket.socket):
        """
        Add a new user to the user_infos dictionary.
        """
        # Read the JSON data from the socket
        raw_json = self.endpoint_manager.readUTF(s)
        if not raw_json:
            return

        # Parse the JSON data into a dictionary
        json_obj = json.loads(raw_json)
        with self.lock:
            try:
                # Extract the username from the JSON data
                username = json_obj.pop("username", None)
                if not username:
                    return self.endpoint_manager.writeUTF(s, "ERROR: Missing argument")

                # Add the user information to the user_infos dictionary
                self.user_infos[username] = json_obj
                # Create the user's directory in the base directory
                user_dir = self.BASE_DIR / username
                user_dir.mkdir(parents=True, exist_ok=True)
                # Send a success message to the client
                self.endpoint_manager.writeUTF(s, "Ok")
            except Exception as e:
                # If an exception occurs, print the error message and send an error message to the client
                print(f"Error adding user: {e}")
                self.endpoint_manager.writeUTF(s, f"ERROR: {e}")
            finally:
                # Write the updated user_infos dictionary to a JSON file
                with open(self.BASE_DIR / "user_infos.json", "w") as f:
                    json.dump(self.user_infos, f, indent=4)

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
