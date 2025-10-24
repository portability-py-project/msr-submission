from socket import socket
from unittest.mock import patch

import pytest
import os

@pytest.fixture
def tlm_listener():
    from plugins.cfs.pycfs.tlm_listener import TlmListener
    return TlmListener("127.0.0.1", 5011)


def test_tlm_listener_init(tlm_listener):
    assert tlm_listener.ipaddr == "127.0.0.1"
    assert tlm_listener.port == 5011
    assert tlm_listener.socket


def test_tlm_listener_cleanup(tlm_listener):
    tlm_listener.cleanup()
    assert tlm_listener.socket._closed


def test_tlm_listener_create_socket(tlm_listener):
    sock = tlm_listener.create_socket()
    assert not sock._closed
    assert not sock.getblocking()
    assert tlm_listener.port == 5011


def test_tlm_listener_get_port(tlm_listener):
    assert tlm_listener.get_port() == tlm_listener.port


def test_tlm_listener_read_socket(tlm_listener):
    with patch.object(tlm_listener, 'socket', spec=socket) as mocksock:
        mocksock.recv.return_value = "bytes received"
        mocksock.fileno.return_value = 1
        assert tlm_listener.read_socket() == "bytes received"
        mocksock.recv.assert_called_once_with(65535)


def test_tlm_listener_read_socket_recreate_socket(tlm_listener):
    tlm_listener.cleanup()
    with patch('socket.socket', spec=socket) as mocksock:
        mocksock.return_value.recv.return_value = "bytes received"
        mocksock.return_value.fileno.return_value = -1
        assert tlm_listener.read_socket() == "bytes received"
        mocksock.return_value.recv.assert_called_once_with(65535)


def test_tlm_listener_read_socket_error(tlm_listener):
    with patch.object(tlm_listener, 'socket', spec=socket) as mocksock:
        mocksock.recv.side_effect = IOError("mock error")
        assert tlm_listener.read_socket() == 0

if os.name == 'nt':
    import win32file
    import msvcrt