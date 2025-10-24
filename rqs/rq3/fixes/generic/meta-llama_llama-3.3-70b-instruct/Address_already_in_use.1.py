import errno
import socket

# Set the CCSDS Max Size to maximum theoretical UDP packet size
#   - This value is used during the tlm_socket.recv() to receive *up to*
#     CCSDS_MAX_SIZE bytes
CCSDS_MAX_SIZE = 65535


class TlmListener:
    def __init__(self, ipaddr, port):
        self.ipaddr = ipaddr
        # Port = 0 will assign a random available port
        self.port = port
        self.socket = self.create_socket()

    def cleanup(self):
        self.socket.close()

    def create_socket(self):
        tlm_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        tlm_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            tlm_socket.bind((self.ipaddr, self.port))
        except socket.error as e:
            if e.errno == errno.EADDRINUSE:
                tlm_socket.bind(('', self.port))
            else:
                raise
        tlm_socket.setblocking(False)
        self.port = tlm_socket.getsockname()[1]
        return tlm_socket

    def get_port(self):
        return self.port

    def read_socket(self):
        received = b''
        if self.socket.fileno() == -1:
            self.socket = self.create_socket()
        try:
            received = self.socket.recv(CCSDS_MAX_SIZE)
        except (IOError, OSError) as exception:
            if exception.errno == errno.EWOULDBLOCK:
                pass
        return received