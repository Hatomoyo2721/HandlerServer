import json
import os
import pathlib
import socket
from threading import Lock

class ShareManager:
    BASE_DIR = pathlib.Path(os.path.dirname(os.path.abspath(__file__)))

    def __init__(self, endpoint_manager):
        self.user_shares = {}
        self.lock = Lock()
        self.endpoint_manager = endpoint_manager

    def add_share_user(self, s: socket.socket):
        """
        Adds a user to the list of users who have access to a share.

        The user's name and the path to the share directory are read from the socket.
        If the share directory does not exist, a new entry for it is created in the
        user_shares dictionary. The user's name is added to the list of users for that
        share directory. The user_shares dictionary is then written to the user_shares.json
        file.

        Args:
            s (socket.socket): The socket object representing the connection to the client.

        Returns:
            str: The response message indicating the success or failure of the operation.
        """
        # Read the username and share path from the socket
        user = self.endpoint_manager.readUTF(s)
        if not user:
            return self.endpoint_manager.writeUTF(s, "ERROR: Missing username")
        share_path = self.endpoint_manager.readUTF(s)
        if not share_path:
            return self.endpoint_manager.writeUTF(s, "ERROR: Missing share_path")

        # Decode the username and share path
        share_path = share_path.decode()
        user = user.decode()
        print(share_path)
        print(user)

        with self.lock:
            try:
                # If the share directory exists in the user_shares dictionary,
                # add the user to the list of users for that share directory.
                # Otherwise, create a new entry for the share directory in the
                # user_shares dictionary and initialize the list of users with the
                # user's name.
                if share_path in self.user_shares:
                    if user not in self.user_shares[share_path]:
                        self.user_shares[share_path].append(user)
                else:
                    self.user_shares[share_path] = [user]
                self.endpoint_manager.writeUTF(s, "OK")
            except Exception as e:
                # If an error occurs, print the error message and send an error
                # response message to the client.
                print(f"Error adding share user: {e}")
                self.endpoint_manager.writeUTF(s, f"ERROR: {e}")
            finally:
                # Write the updated user_shares dictionary to the user_shares.json file.
                with open(self.BASE_DIR / "user_shares.json", "w") as f:
                    json.dump(self.user_shares, f, indent=4)

    def get_share_users(self, s: socket.socket):
        """
        Gets the list of users who have access to a share.

        The path to the share directory is read from the socket. If the share
        directory exists in the user_shares dictionary, the list of users for
        that share directory is sent to the client. If the share directory does
        not exist, an empty string is sent to the client.

        Args:
            s (socket.socket): The socket object representing the connection to the client.

        Returns:
            str: The response message indicating the success or failure of the operation.
        """
        share_path = self.endpoint_manager.readUTF(s)
        if not share_path:
            return

        # Decode the share path
        share_path = share_path.decode()

        with self.lock:
            try:
                # If the share directory exists in the user_shares dictionary,
                # send the list of users for that share directory to the client.
                # Otherwise, send an empty string to the client.
                if share_path in self.user_shares:
                    self.endpoint_manager.writeUTF(s, ",".join(self.user_shares[share_path]))
                else:
                    self.endpoint_manager.writeUTF(s, "")
            except Exception as e:
                # If an error occurs, print the error message and send an error
                # response message to the client.
                print(f"Error getting share users: {e}")
                self.endpoint_manager.writeUTF(s, f"ERROR: {e}")