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
        self.load_user_infos()
        self.load_user_shares()
        self.register_endpoints()

    def register_endpoints(self):
        self.endpoints_mapping['index'] = self.index
        self.endpoints_mapping['add_user'] = self.user_manager.add_user
        self.endpoints_mapping['upload'] = self.user_manager.upload
        self.endpoints_mapping['add_share_user'] = self.share_manager.add_share_user
        self.endpoints_mapping['get_share_users'] = self.share_manager.get_share_users

    @staticmethod
    def readUTF(s: socket.socket):
        data = s.recv(2)
        if not data:
            return
        length = struct.unpack("!H", data)
        data = s.recv(length[0])
        return data

    @staticmethod
    def writeUTF(s: socket.socket, msg: str):
        return
        data = bytearray(msg, "utf8")
        size = len(data)
        s.sendall(struct.pack("!H", size))
        s.sendall(data)

    def recv_code(self, s: socket.socket):
        try:
            code = self.readUTF(s)
            if not code:
                return
            code = code.decode()
            print("\nCode: {}".format(code))
            self.endpoints_mapping[code](s)
        except Exception as err:
            print(err)
        finally:
            if s._closed:
                return
            s.close()

    def index(self, s: socket.socket):
        while True:
            data = self.readUTF(s)
            if not data:
                break
            print(data)
        s.close()

    def load_user_infos(self):
        if (self.BASE_DIR / "user_infos.json").exists():
            with open(self.BASE_DIR / "user_infos.json") as f:
                self.user_manager.user_infos = json.load(f)

    def load_user_shares(self):
        if pathlib.Path(self.BASE_DIR / "user_infos.json").exists():
            with open(self.BASE_DIR / "user_infos.json") as f:
                self.share_manager.user_shares = json.load(f)

    def save_user_infos(self):
        with open(self.BASE_DIR / "user_shares.json", "w") as f:
            json.dump(self.user_manager.user_infos, f, indent=4)

    def save_user_shares(self):
        with open(self.BASE_DIR / "user_shares.json", "w") as f:
            json.dump(self.share_manager.user_shares, f, indent=4)
