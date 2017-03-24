"""ANCP Client

Copyright 2017 Christian Giese <cgiese@juniper.net>
"""
from __future__ import print_function
from __future__ import unicode_literals
from builtins import bytes
from ancp.subscriber import Subscriber
from datetime import datetime
from threading import Thread
from threading import Event
import struct
import socket
import logging


VERSION_RFC = 50

# MESSAGE TYPE
ADJACENCY = 10
PORT_MANAGEMENT = 32
PORT_UP = 80
PORT_DOWN = 81
ADJACENCY_UPDATE = 85

# ADJACENCY STATE
IDLE = 1
SYNSENT = 2
SYNRCVD = 3
ESTAB = 4

# ADJACENCY MESSAGE CODE
SYN = 1
SYNACK = 2
ACK = 3
RSTACK = 4

# TECH TYPES
ANY = 0
PON = 1
DSL = 5

# RESULT FIELDS
Ignore = 0x00
Nack = 0x01
AckAll = 0x02
Success = 0x03
Failure = 0x04

# RESULT CODES
NoResult = 0x000

# CAPABILITIES
TOPO = 1
OAM = 4


# HELPER FUNCTIONS AND CALSSES ------------------------------------------------

def tomac(v):
    """Tuple to MAC Address

    :param v: MAC address
    :type v: tuple
    :return: MAC address
    :rtype: str
    """
    return "%02x:%02x:%02x:%02x:%02x:%02x" % v


# ANCP CLIENT -----------------------------------------------------------------

class Client(object):
    """ANCP Client

    :param address: ANCP server address
    :type address: str
    :param port: ANCP port (default: 6086)
    :type port: int
    :param tech_type: tech type (default=DSL)
    :type tech_type: int
    """
    def __init__(self, address, port=6068, tech_type=DSL):
        self.address = address
        self.port = port

        self.timer = 25.0   # adjacency timer
        self.timeout = 1.0  # socket timeout
        self._last_syn_time = None

        self.established = Event()
        self.version = VERSION_RFC
        self.tech_type = tech_type
        self.state = IDLE
        self.capabilities = [TOPO]
        self.transaction_id = 1
        self.sender_name = (1, 2, 3,  4, 5, 6)
        self.sender_instance = 16777217
        self.sender_port = 0
        self.receiver_name = (0, 0, 0,  0, 0, 0)
        self.receiver_instance = 0
        self.receiver_port = 0
        # TCP SOCKET
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        """connect"""
        self.socket.connect((self.address, self.port))
        self.socket.setblocking(True)
        self.socket.settimeout(self.timeout)
        self._send_syn()
        # rx / tx thread
        self._thread = Thread(target=self._handle, name="handle")
        self._thread.setDaemon(True)
        self._thread.start()
        self.established.wait()

    def disconnect(self, send_ack=False):
        """disconnect"""
        if send_ack:
            self._send_ack()
        else:
            self._send_rstack()
        self._thread.join(timeout=1.0)
        self.socket.close()
        self.established.clear()

    def port_up(self, subscriber):
        """send port-up message

        :param subscriber: ANCP subscriber
        :type subscriber: ancp.subscriber.Subscriber
        """
        self._port_updown(PORT_UP, subscriber)

    def port_down(self, subscriber):
        """send port-down message

        :param subscriber: ANCP subscriber
        :type subscriber: ancp.subscriber.Subscriber
        """
        self._port_updown(PORT_DOWN, subscriber)

    # internal methods --------------------------------------------------------

    def _handle(self):
        """RX / TX Thread"""
        log = logging.getLogger(__name__)
        while True:
            try:
                b = self._recvall(4)
            except socket.timeout:
                self._handle_timeout()
            else:
                if len(b) == 0:
                    log.warning("connection lost with %s " % tomac(self.receiver_name))
                    break
                else:
                    log.debug("received len(b) = %d" % len(b))
                    (id, length) = struct.unpack("!HH", b)
                    log.debug("message rcvd length field %d" % length)
                    if id != 0x880C:
                        log.error("incorrect ident 0x%x" % id)
                        break
                    b = self._recvall(length)
                    if len(b) != length:
                        log.warning("MSG_WAITALL failed")
                    log.debug("rest received len(b) = %d" % len(b))
                    (ver, mtype, var) = struct.unpack_from("!BBH", b, 0)
                    s0 = self.state
                    if mtype == ADJACENCY:
                        self._handle_adjacency(var, b)
                    elif mtype == ADJACENCY_UPDATE:
                        self._handle_adjacency_update(var, b)
                    elif mtype == PORT_UP:
                        pass
                    elif mtype == PORT_DOWN:
                        pass
                    else:
                        self._handle_general(var, b)
                    if s0 != self.state and self.state == ESTAB and not self.established.is_set():
                        self.established.set()
                        log.info("adjacency established with %s" % tomac(self.receiver_name))
        self.established.clear()

    def _port_updown(self, message_type, subscriber):
        if not self.established.is_set():
            raise RuntimeError("session not established")
        if not isinstance(subscriber, Subscriber):
            raise ValueError("invalid subscriber")

        num_tlvs, tlvs = subscriber.tlvs
        self._send_port_updwn(message_type, self.tech_type, num_tlvs, tlvs)

    def _recvall(self, toread):
        buf = bytearray(toread)
        view = memoryview(buf)
        while toread:
            nbytes = self.socket.recv_into(view, toread)
            if nbytes == 0:
                return b''
            view = view[nbytes:]    # slicing views is cheap
            toread -= nbytes

        return buf

    def _mkadjac(self, mtype, time, m, code):
        totcapslen = len(self.capabilities) * 4
        b = bytearray(40 + totcapslen)
        off = 0
        struct.pack_into("!HH", b, off, 0x880c, 36 + totcapslen)
        off += 4
        struct.pack_into("!BBBB", b, off, self.version, mtype, int(self.timer * 10), (m << 7) | code)
        off += 4
        (s1, s2, s3, s4, s5, s6) = self.sender_name
        (r1, r2, r3, r4, r5, r6) = self.receiver_name
        struct.pack_into("!6B6B", b, off,
                         s1, s2, s3, s4, s5, s6,
                         r1, r2, r3, r4, r5, r6)
        off += 12
        struct.pack_into("!II", b, off, self.sender_port, self.receiver_port)
        off += 8
        struct.pack_into("!I", b, off, self.sender_instance)
        off += 4
        struct.pack_into("!I", b, off, self.receiver_instance)
        off += 5
        struct.pack_into("!BH", b, off, len(self.capabilities), totcapslen)
        off += 3
        for cap in self.capabilities:
            struct.pack_into("!H", b, off, cap)
            off += 2
        return b

    def _send_adjac(self, m, code):
        log = logging.getLogger(__name__)
        log.debug("send adjanecy message with code %s" % (code))
        b = self._mkadjac(ADJACENCY, self.timer * 10, m, code)
        self.socket.send(b)

    def _send_syn(self):
        self._send_adjac(0, SYN)
        self.state = SYNSENT
        self._last_syn_time = datetime.now()

    def _send_ack(self):
        self._send_adjac(0, ACK)

    def _send_synack(self):
        self._send_adjac(0, SYNACK)
        self.state = SYNRCVD

    def _send_rstack(self):
        self._send_adjac(0, RSTACK)
        self.state = SYNRCVD

    def _handle_timeout(self):
        if self.state == SYNSENT:
            self._send_syn()
        elif self.state == ESTAB:
            # send every self.timer seconds a SYN, ... (keep-alive)
            diff = datetime.now() - self._last_syn_time
            if diff.seconds >= self.timer:
                self._send_syn()

    def _handle_syn(self):
        log = logging.getLogger(__name__)
        log.debug("SYN received with current state %d" % self.state)
        if self.state == SYNSENT:
            self._send_synack()
        elif self.state == SYNRCVD:
            self._send_synack()
        elif self.state == ESTAB:
            self._send_ack()
        elif self.state == IDLE:
            self._send_syn()
        else:
            pass

    def _handle_synack(self):
        log = logging.getLogger(__name__)
        log.debug("SYNACK received with current state %d" % self.state)
        if self.state == SYNSENT:
            # C !C ??
            self._send_ack()
            self.state = ESTAB
        elif self.state == SYNRCVD:
            # C !C ??
            self._send_ack()
        elif self.state == ESTAB:
            self._send_ack()
        else:
            pass

    def _handle_ack(self):
        log = logging.getLogger(__name__)
        log.debug("ACK received with current state %d" % self.state)
        if self.state == ESTAB:
            self._send_ack()
        else:
            self.state = ESTAB

    def _handle_rstack(self):
        log = logging.getLogger(__name__)
        log.debug("RSTACK received with current state %d" % self.state)
        if self.state == SYNSENT:
            pass
        else:
            # disconnect
            self.disconnect(send_ack=True)

    def _handle_adjacency(self, var, b):
        log = logging.getLogger(__name__)
        timer = var >> 8
        m = var & 0x80
        code = var & 0x7f
        if m == 1:
            # ignore, must be 0 as we are the server
            pass
        self.receiver_name = struct.unpack_from("!BBBBBB", b, 4)
        self.receiver_instance = struct.unpack_from("!I", b, 24)[0] & 16777215
        if code == SYN:
            self._handle_syn()
        elif code == SYNACK:
            self._handle_synack()
        elif code == ACK:
            self._handle_ack()
        elif code == RSTACK:
            self._handle_rstack()
        else:
            log.warning("unknown code %d" % code)

    def _handle_adjacency_update(self, var, b):
        res = var >> 12
        code = var & 0xfff

    def _handle_general(self, var, b):
        pass

    def _mkgeneral(self, message_type, result, result_code, body):
        b = bytearray(4 + 12)
        partition_id = 0
        off = 0
        struct.pack_into("!HH", b, off, 0x880c, len(b) - 4 + len(body))
        off += 4
        struct.pack_into("!BBH", b, off, self.version, message_type, (result << 12) | result_code)
        off += 4
        struct.pack_into("!I", b, off, (partition_id << 24) | self.transaction_id)
        self.transaction_id += 1
        off += 4
        struct.pack_into("!HH", b, off, 0x8001, len(b) - 4 + len(body))
        off += 4
        return b + body

    def _send_port_updwn(self, message_type, tech_type, num_tlvs, tlvs):
        b = bytearray(28)
        off = 20
        struct.pack_into("!xBBx", b, off, message_type, tech_type)
        off += 4
        struct.pack_into("!HH", b, off, num_tlvs, len(tlvs))
        off += 4
        msg = self._mkgeneral(message_type, Nack, NoResult, b + tlvs)
        self.socket.send(msg)
