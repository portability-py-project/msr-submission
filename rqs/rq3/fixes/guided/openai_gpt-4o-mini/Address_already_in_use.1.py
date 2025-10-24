import errno
import socket
import time

CCSDS_MAX_SIZE = 65535

class TlmListener:
    def __init__(self, ipaddr, port):
        self.ipaddr = ipaddr
        self.port = port
        self.socket = self.create_socket()

    def cleanup(self):
        self.socket.close()

    def create_socket(self):
        tlm_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        tlm_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        while True:
            try:
                tlm_socket.bind((self.ipaddr, self.port))
                break
            except OSError:
                time.sleep(1)  # Wait before retrying
        tlm_socket.setblocking(False)
        self.port = tlm_socket.getsockname()[1]
        return tlm_socket

    def get_port(self):
        return self.port

    def read_socket(self):
        received = 0
        if self.socket.fileno() == -1:
            self.socket = self.create_socket()
        try:
            received = self.socket.recv(CCSDS_MAX_SIZE)
        except IOError as exception:
            if exception.errno == errno.EWOULDBLOCK:
                pass
        return received