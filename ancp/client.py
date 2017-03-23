"""Python ANCP Client
"""
from __future__ import print_function
from __future__ import unicode_literals
from ancp import packet
from ancp.subscriber import Subscriber
from datetime import datetime
from threading import Thread
import struct
import socket
import logging

log = logging.getLogger("ancp")


class Client(object):

    def __init__(self, address, port=6068, tech_type=packet.DSL):
        self.address = address
        self.port = port

        self.timer = 25.0   # adjacency timer
        self.timeout = 1.0  # socket timeout
        self._last_syn_time = None

        self.established = False
        self.version = packet.RFC
        self.tech_type = tech_type
        self.state = packet.IDLE
        self.capabilities = [packet.TOPO]
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
        self.socket.connect((self.address, self.port))
        self.socket.setblocking(True)
        self.socket.settimeout(self.timeout)
        self._send_syn()
        # rx / tx thread
        self._thread = Thread(target=self._handle, name="handle")
        self._thread.setDaemon(True)
        self._thread.start()

    def _handle(self):
        """RX / TX Thread"""
        while True:
            try:
                b = self._recvall(4)
            except socket.timeout:
                self._handle_timeout()
            else:
                if len(b) == 0:
                    log.warning("connection lost with %s " % self._tomac(self.receiver_name))
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
                    if mtype == packet.ADJACENCY:
                        self._handle_adjacency(var, b)
                    elif mtype == packet.ADJACENCY_UPDATE:
                        self._handle_adjacency_update(var, b)
                    elif mtype == packet.PORT_UP:
                        pass
                    elif mtype == packet.PORT_DOWN:
                        pass
                    else:
                        self._handle_general(var, b)
                    if s0 != self.state and self.state == packet.ESTAB and not self.established:
                        self.established = True
                        log.info("adjacency established with %s" % self._tomac(self.receiver_name))

    def disconnect(self):
        self._send_rstack()
        self._thread.join()
        self.socket.close()

    def port_up(self, subscriber):
        self._port_updown(packet.PORT_UP, subscriber)

    def port_down(self, subscriber):
        self._port_updown(packet.PORT_DOWN, subscriber)

    # internal methods --------------------------------------------------------
    def _port_updown(self, message_type, subscriber):
        if not self.established:
            raise RuntimeError("session not established")
        if not isinstance(subscriber, Subscriber):
            raise ValueError("invalid subscriber")

        num_tlvs, tlvs = subscriber.tlvs
        self._send_port_updwn(packet.PORT_UP, self.tech_type, num_tlvs, tlvs)

    @staticmethod
    def _tomac(v):
        return "%02x:%02x:%02x:%02x:%02x:%02x" % v

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
        struct.pack_into("!BBBB", b, off, self.version, mtype, self.timer * 10, (m << 7) | code)
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
        log.debug("send adjanecy message with code %s" % (code))
        b = self._mkadjac(packet.ADJACENCY, self.timer * 10, m, code)
        self.socket.send(b)

    def _send_syn(self):
        self._send_adjac(0, packet.SYN)
        self.state = packet.SYNSENT
        self._last_syn_time = datetime.now()

    def _send_ack(self):
        self._send_adjac(0, packet.ACK)

    def _send_synack(self):
        self._send_adjac(0, packet.SYNACK)
        self.state = packet.SYNRCVD

    def _send_rstack(self):
        self._send_adjac(0, packet.RSTACK)
        self.state = packet.SYNRCVD

    def _handle_timeout(self):
        if self.state == packet.SYNSENT:
            self._send_syn()
        elif self.state == packet.ESTAB:
            # send every self.timer seconds a SYN, ... (keep-alive)
            diff = datetime.now() - self._last_syn_time
            if diff.seconds >= self.timer:
                self._send_syn()

    def _handle_syn(self):
        log.debug("SYN received with current state %d" % self.state)
        if self.state == packet.SYNSENT:
            self._send_synack()
        elif self.state == packet.SYNRCVD:
            self._send_synack()
        elif self.state == packet.ESTAB:
            self._send_ack()
        elif self.state == packet.IDLE:
            self._send_syn()
        else:
            pass

    def _handle_synack(self):
        log.debug("SYNACK received with current state %d" % self.state)
        if self.state == packet.SYNSENT:
            # C !C ??
            self._send_ack()
            self.state = packet.ESTAB
        elif self.state == packet.SYNRCVD:
            # C !C ??
            self._send_ack()
        elif self.state == packet.ESTAB:
            self._send_ack()
        else:
            pass

    def _handle_ack(self):
        log.debug("ACK received with current state %d" % self.state)
        if self.state == packet.ESTAB:
            self._send_ack()
        else:
            self.state = packet.ESTAB

    def _handle_rstack(self):
        log.debug("RSTACK received with current state %d" % self.state)
        if self.state == packet.SYNSENT:
            pass
        else:
            # TODO: reset link
            pass

    def _handle_adjacency(self, var, b):
        timer = var >> 8
        m = var & 0x80
        code = var & 0x7f
        if m == 1:
            # ignore, must be 0 as we are the server
            pass
        self.receiver_name = struct.unpack_from("!BBBBBB", b, 4)
        self.receiver_instance = struct.unpack_from("!I", b, 24)[0] & 16777215
        if code == packet.SYN:
            self._handle_syn()
        elif code == packet.SYNACK:
            self._handle_synack()
        elif code == packet.ACK:
            self._handle_ack()
        elif code == packet.RSTACK:
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
        msg = self._mkgeneral(message_type, packet.Nack, packet.NoResult, b + tlvs)
        self.socket.send(msg)
