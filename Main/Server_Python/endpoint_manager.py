from asyncio import Server
import socket
import struct
import os
import pathlib
import logging
import traceback
from user_manager import UserManager
from share_manager import ShareManager

class EndpointManager:
    BASE_DIR = pathlib.Path(__file__).resolve().parent

    def __init__(self, server):
        self.server = server
        self.endpoints_mapping = {}
        self.user_manager = UserManager(self)
        self.share_manager = ShareManager(self)
        self.register_endpoints()

    def register_endpoints(self):
        self.endpoints_mapping['add_user'] = self.user_manager.add_user
        self.endpoints_mapping['create_directory'] = self.user_manager.create_directory
        self.endpoints_mapping['load_directory'] = self.user_manager.load_directory
        self.endpoints_mapping['add_share_user'] = self.share_manager.add_share_user
        self.endpoints_mapping['get_share_users'] = self.share_manager.get_share_users

    @staticmethod
    def readUTF(s: socket.socket):
        try:
            data_length = struct.unpack("!H", s.recv(2))[0]
            data = s.recv(data_length).decode('utf-8')
            return data
        except Exception as e:
            logging.error(f"Error reading UTF-8 data: {e}\n{traceback.format_exc()}")
            return None

    @staticmethod
    def writeUTF(s: socket.socket, msg: str):
        try:
            data = msg.encode('utf-8')
            length = struct.pack("!H", len(data))
            s.sendall(length + data)
        except Exception as e:
            logging.error(f"Error writing UTF: {e}\n")

    def recv_code(self, s: socket.socket):
        try:
            code = self.readUTF(s)
            if not code:
                return
            logging.info(f"Code: {code}\n")
            if code in self.endpoints_mapping:
                self.endpoints_mapping[code](s)
            else:
                logging.warning(f"Unknown code: {code}\n")
        except Exception as err:
            logging.error(f"Error receiving code: {err}\n")
        finally:
            s.close()