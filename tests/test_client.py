"""ANCP Client Tests

Copyright (C) 2017-2024, Christian Giese (GIC-de)
SPDX-License-Identifier: MIT
"""
from ancp.client import *
from ancp.subscriber import Subscriber
from mock import MagicMock
import pytest
import time
import logging
import sys

# setup logging to stdout
log = logging.getLogger()
log.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
handler.setFormatter(logging.Formatter('%(asctime)-15s [%(levelname)-8s] %(message)s'))
log.addHandler(handler)


@pytest.fixture(scope="module")
def ancp_client():
    client = Client(address="1.2.3.4")
    client.socket = MagicMock()
    # socket rx/tx mock
    client._rx_bytes = bytearray()
    client._tx_bytes = bytearray()

    def _rx(b):
        off = 0
        length = 0
        while True:
            if off <= len(b):
                length = yield b[off-length:off]
                off += length
            else:
                time.sleep(1.0)
    rx = _rx(client._rx_bytes)
    next(rx)
    client._recvall = rx.send

    def tx(msg):
        client._tx_bytes += msg

    client.socket.send = tx
    return client


def test_tomac():
    mac = tomac((1, 2, 3,  4, 5, 6))
    assert mac == "01:02:03:04:05:06"


def test_connect(ancp_client):
    ancp_client._rx_bytes += ancp_client._mkadjac(MessageType.ADJACENCY, ancp_client.timer * 10, 1, MessageCode.SYNACK)
    ancp_client._rx_bytes += ancp_client._mkadjac(MessageType.ADJACENCY, ancp_client.timer * 10, 1, MessageCode.ACK)

    ancp_client.connect()
    assert ancp_client.established.is_set() == True
    assert ancp_client.state == AdjacencyState.ESTAB


def test_port_up(ancp_client):
    S1 = Subscriber(aci="0.0.0.0/0.0.0.0 eth 1/1:7", up=1024, down=16000)
    S2 = Subscriber(aci="0.0.0.0/0.0.0.0 eth 2/2:7", up=1024, down=16000)
    subscribers = [S1, S2]
    tx_off = len(ancp_client._tx_bytes)
    ancp_client.port_up(subscribers)

    msg = ancp_client._tx_bytes[tx_off:]

    off = 0
    for s in subscribers:
        length, code = struct.unpack_from("!HxB", msg, 2 + off)
        assert code == MessageType.PORT_UP
        off += length + 4
    assert len(msg) == off


def test_port_down(ancp_client):
    S1 = Subscriber(aci="0.0.0.0/0.0.0.0 eth 1/1:7", up=1024, down=16000)
    S2 = Subscriber(aci="0.0.0.0/0.0.0.0 eth 2/2:7", up=1024, down=16000)
    subscribers = [S1, S2]
    tx_off = len(ancp_client._tx_bytes)
    ancp_client.port_down(subscribers)

    msg = ancp_client._tx_bytes[tx_off:]

    off = 0
    for s in subscribers:
        length, code = struct.unpack_from("!HxB", msg, 2 + off)
        assert code == MessageType.PORT_DOWN
        off += length + 4
    assert len(msg) == off


def test_disconnect(ancp_client):
    tx_off = len(ancp_client._tx_bytes)
    ancp_client.disconnect()
    msg = ancp_client._tx_bytes[tx_off:]
    length, code = struct.unpack_from("!HxxxB", msg, 2)
    assert code == MessageCode.RSTACK
    assert ancp_client.established.is_set() == False
    assert ancp_client.state != AdjacencyState.ESTAB
