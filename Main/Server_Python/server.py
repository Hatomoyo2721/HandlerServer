import threading
import socket
from endpoint_manager import EndpointManager

class Server:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.endpoint_manager = EndpointManager(self)
        self.lock = threading.Lock()

    def start(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.host, self.port))
            print("Socket binded to port", self.port)
            s.listen(5)
            while True:
                try:
                    c, addr = s.accept()
                    print("\nGot connection from", addr)
                    threading.Thread(target=self.endpoint_manager.recv_code, args=(c,), daemon=True).start()
                except KeyboardInterrupt:
                    print("Server is shutting down...")
                except Exception as e:
                    print(f"Error: {e}")

if __name__ == "__main__":
    server = Server("127.0.0.1", 1234)
    server.start()