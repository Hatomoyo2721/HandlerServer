import socket
import threading
import logging
from endpoint_manager import EndpointManager  

class Server:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.setup_logging()
        self.endpoint_manager = EndpointManager(self)

    def setup_logging(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    def start(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind((self.host, self.port))
                s.listen(5)
                logging.info(f"Server started on port {self.port}")
                while True:
                    c, addr = s.accept()
                    logging.info(f"Connection from {addr}")
                    threading.Thread(target=self.endpoint_manager.recv_code, args=(c,), daemon=True).start()
            except Exception as e:
                logging.error(f"Error: {e}")

if __name__ == "__main__":
    server = Server("127.0.0.1", 1234)
    server.start()
