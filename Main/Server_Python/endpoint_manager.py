import socket
import struct
import json
import os
import pathlib
from user_manager import UserManager
from share_manager import ShareManager

class EndpointManager:
    BASE_DIR = pathlib.Path(os.path.dirname(os.path.abspath(__file__)))

    def __init__(self, server):
        self.server = server
        self.endpoints_mapping = {}
        self.user_manager = UserManager(self)
        self.share_manager = ShareManager(self)
        self.register_endpoints()

    def register_endpoints(self):
        self.endpoints_mapping['index'] = self.index
        self.endpoints_mapping['add_user'] = self.user_manager.add_user
        self.endpoints_mapping['upload'] = self.user_manager.upload
        self.endpoints_mapping['create_directory'] = self.user_manager.create_directory
        self.endpoints_mapping['list_directory'] = self.user_manager.list_directory
        self.endpoints_mapping['list_directory'] = self.user_manager.list_directory
        self.endpoints_mapping['add_share_user'] = self.share_manager.add_share_user
        self.endpoints_mapping['get_share_users'] = self.share_manager.get_share_users
        
    @staticmethod
    def readUTF(s: socket.socket):
        try:
            data = s.recv(2)
            if not data:
                return None
            length = struct.unpack("!H", data)[0]
            data = s.recv(length)
            return data
        except Exception as e:
            print(f"Error reading UTF: {e}")
            return None

    @staticmethod
    def writeUTF(s: socket.socket, msg: str):
        return

    def recv_code(self, s: socket.socket):
        try:
            code = self.readUTF(s)
            if not code:
                return
            code = code.decode()
            print("\nCode: {}".format(code))
            if code in self.endpoints_mapping:
                self.endpoints_mapping[code](s)
            else:
                print(f"Unknown code: {code}")
        except Exception as err:
            print(f"Error receiving code: {err}")
        finally:
            if s._closed:
                return
            s.close()

    def index(self, s: socket.socket):
        while True:
            data = self.readUTF(s)
            if not data:
                break
            print(data.decode())
        s.close()