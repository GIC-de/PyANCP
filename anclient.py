from __future__ import print_function
import gevent
import gevent.socket
import struct
import socket

#
# Requirements: python3, gevent
#
# pip3 install gevent
#
#


class Config:
    def __init__(self):
        self.server = ('172.30.138.10', 6068)
        self.sender_name = (1, 2, 3,  4, 5, 6)

        self.tlvs = [mkcircuitid_tlv(b"1/1/100")]
        self.tech_type = Ctx.PON


class TLV:
    def __init__(self, t, val):
        self.t = t
        self.len = len(val)
        padl = 4 - (self.len % 4)
        if(padl < 4):
            self.val = val + bytearray(padl)
        else:
            self.val = val


class Ctx(object):
    VERSION = 50

    #
    # message types
    #
    ADJACENCY = 10
    PORT_MANAGEMENT = 32
    PORT_UP = 80
    PORT_DOWN = 81
    ADJACENCY_UPDATE = 85

    #
    # adjacency state
    #
    IDLE = 1
    SYNSENT = 2
    SYNRCVD = 3
    ESTAB = 4

    #
    # adjacency message codes
    #
    SYN = 1
    SYNACK = 2
    ACK = 3
    RSTACK = 4

    #
    # tech types
    #
    ANY = 0
    PON = 1
    DSL = 5

    #
    # result field
    #
    Ignore = 0x00
    Nack = 0x01
    AckAll = 0x02
    Success = 0x03
    Failure = 0x04

    #
    # result code
    #
    NoResult = 0x000

    def __init__(self):
        self.receiver_name = (0, 0, 0,  0, 0, 0)
        self.sender_port = 0
        self.receiver_port = 0
        self.sender_instance = 16777217
        self.receiver_instance = 0
        self.timeout = None
        self.state = self.IDLE
        self.caps = [1]  # 1 = Topo / 4 = OAM
        self.transaction_id = 1
        self.config = Config()


def tomac(v):
    return "%02x:%02x:%02x:%02x:%02x:%02x" % v


def recvall(s, toread):
    buf = bytearray(toread)
    view = memoryview(buf)
    while toread:
        nbytes = s.recv_into(view, toread)
        if nbytes == 0:
            return b''
        view = view[nbytes:]    # slicing views is cheap
        toread -= nbytes

    return buf


def mkadjac(ctx, mtype, timer, m, code):
    totcapslen = len(ctx.caps) * 4
    b = bytearray(40 + totcapslen)
    off = 0
    struct.pack_into("!HH", b, off, 0x880c, 36 + totcapslen)
    off += 4
    struct.pack_into("!BBBB", b, off, ctx.VERSION, mtype, timer, (m << 7) | code)
    off += 4
    (s1, s2, s3, s4, s5, s6) = ctx.config.sender_name
    (r1, r2, r3, r4, r5, r6) = ctx.receiver_name
    struct.pack_into("!6B6B", b, off,
                     s1, s2, s3, s4, s5, s6,
                     r1, r2, r3, r4, r5, r6)
    off += 12
    struct.pack_into("!II", b, off, ctx.sender_port, ctx.receiver_port)
    off += 8
    struct.pack_into("!I", b, off, ctx.sender_instance)
    off += 4
    struct.pack_into("!I", b, off, ctx.receiver_instance)
    off += 5
    struct.pack_into("!BH", b, off, len(ctx.caps), totcapslen)
    off += 3
    for cap in ctx.caps:
        struct.pack_into("!H", b, off, cap)
        off += 2

    return b


def send_adjac(s, ctx, m, code):
    b = mkadjac(ctx, Ctx.ADJACENCY, 250, m, code)
    s.send(b)


def send_syn(s, ctx):
    send_adjac(s, ctx, 0, Ctx.SYN)
    ctx.timeout = 25.
    ctx.state = Ctx.SYNSENT


def send_ack(s, ctx):
    send_adjac(s, ctx, 0, Ctx.ACK)
    ctx.timeout = 25.


def send_synack(s, ctx):
    send_adjac(s, ctx, 0, Ctx.SYNACK)
    ctx.timeout = 25.
    ctx.state = Ctx.SYNRCVD


def handle_timeout(s, ctx):
    if ctx.state == Ctx.IDLE:
        pass
    elif ctx.state == Ctx.SYNSENT:
        send_syn(s, ctx)
    elif ctx.state == Ctx.ESTAB:
        send_ack(s, ctx)
    else:
        pass


def handle_syn(s, ctx, var):
    print("SYN rcvd state %d" % ctx.state)
    if ctx.state == Ctx.SYNSENT:
        send_synack(s, ctx)
    elif ctx.state == Ctx.SYNRCVD:
        send_synack(s, ctx)
    elif ctx.state == Ctx.ESTAB:
        send_ack(s, ctx)
    elif ctx.state == Ctx.IDLE:
        send_syn(s, ctx)
    else:
        pass


def handle_synack(s, ctx, var):
    if ctx.state == Ctx.SYNSENT:
        # C !C ??
        send_ack(s, ctx)
        ctx.state = Ctx.ESTAB
    elif ctx.state == Ctx.SYNRCVD:
        # C !C ??
        send_ack(s, ctx)
    elif ctx.state == Ctx.ESTAB:
        send_ack(s, ctx)
    else:
        pass


def handle_ack(s, ctx, var):
    if ctx.state == Ctx.SYNSENT:
        send_rstack(s, ctx)
    elif ctx.state == Ctx.SYNRCVD:
        # B? C?
        send_ack(s, ctx)
        ctx.state = Ctx.ESTAB
    elif ctx.state == Ctx.ESTAB:
        # send_ack(s, ctx)
        pass
    else:
        pass


def handle_rstack(s, ctx, var):
    if ctx.state == Ctx.SYNSENT:
        pass
    else:
        # TODO, reset link
        pass


def handle_adjacency(s, ctx, var, b):
    timer = var >> 8
    m = var & 0x80
    code = var & 0x7f
    if m == 1:
        # ignore, must be 0 as we are the server
        pass
    ctx.receiver_name = struct.unpack_from("!BBBBBB", b, 4)
    ctx.receiver_instance = struct.unpack_from("!I", b, 24)[0] & 16777215
    print(ctx.receiver_instance)
    if code == Ctx.SYN:
        handle_syn(s, ctx, var)
    elif code == Ctx.SYNACK:
        handle_synack(s, ctx, var)
    elif code == Ctx.ACK:
        handle_ack(s, ctx, var)
    elif code == Ctx.RSTACK:
        handle_rstack(s, ctx, var)
    else:
        print("unknown code %d" % code)


def handle_adjacency_update(s, ctx, var, b):
    res = var >> 12
    code = var & 0xfff


def handle_general(s, ctx, var, b):
    pass


def mkcircuitid_tlv(circuit_id):
    return TLV(0x0001, circuit_id)


def mkremoteid_tlv(remote_id):
    return TLV(0x0002, remote_id)


def mklineattr_tlv(dsl_type, up, down):

    return TLV(0x0004, remote_id)


def mkgeneral(ctx, message_type, result, result_code, body):
    b = bytearray(4 + 12)
    partition_id = 0
    off = 0
    struct.pack_into("!HH", b, off, 0x880c, len(b) - 4 + len(body))
    off += 4
    struct.pack_into("!BBH", b, off, Ctx.VERSION, message_type, (result << 12) | result_code)
    off += 4
    struct.pack_into("!I", b, off, (partition_id << 24) | ctx.transaction_id)
    off += 4
    struct.pack_into("!HH", b, off, 0x8001, len(b) - 4 + len(body))
    off += 4

    return b + body


def mktlvs(tlvs):
    blen = 0
    for i in tlvs:
        blen += 4 + len(i.val)
    b = bytearray(blen)
    off = 0
    for i in tlvs:
        fmt = "!HH%ds" % len(i.val)
        struct.pack_into(fmt, b, off, i.t, i.len, str(i.val))
        off += 4 + len(i.val)

    return b


def send_port_updwn(s, ctx, message_type, tech_type, num_tlvs, tlvs):
    b = bytearray(28)
    off = 20
    struct.pack_into("!xBBx", b, off, message_type, tech_type)
    off += 4
    struct.pack_into("!HH", b, off, num_tlvs, len(tlvs))
    off += 4
    print("DEBUG")
    print(len(tlvs))
    msg = mkgeneral(ctx, message_type, Ctx.Ignore, Ctx.NoResult, b + tlvs)
    s.send(msg)


def send_port_up(s, ctx):
    tlvs = mktlvs(ctx.config.tlvs)
    stlvs = mkslvs(ctx.config.stlvs)
    send_port_updwn(s, ctx, Ctx.PORT_UP, ctx.config.tech_type, len(ctx.config.tlvs), tlvs)


def handle(s):
    ctx = Ctx()
    print("#1handle")
    s.setblocking(True)
    send_syn(s, ctx)
    while True:
        print("#2handle")
        if ctx.timeout is not None:
            b = None
            with gevent.Timeout(ctx.timeout, False):
                b = recvall(s, 4)
        else:
            b = recvall(s, 4)
        if b is None:
            print("timeout")
            handle_timeout(s, ctx)
            ctx.timeout = None
        elif len(b) == 0:
            print("connection lost with %s " % tomac(ctx.receiver_name))
            return
        else:
            print("received len(b) = %d" % len(b))
            (id, length) = struct.unpack("!HH", b)
            print("message rcvd length field %d" % length)
            if id != 0x880C:
                print("incorrect ident 0x%x" % id)
                return
            b = recvall(s, length)
            if len(b) != length:
                print("MSG_WAITALL failed")
            print("rest received len(b) = %d" % len(b))
            (ver, mtype, var) = struct.unpack_from("!BBH", b, 0)
            s0 = ctx.state
            if mtype == Ctx.ADJACENCY:
                handle_adjacency(s, ctx, var, b)
            elif mtype == Ctx.ADJACENCY_UPDATE:
                handle_adjacency_update(s, ctx, var, b)
            elif mtype == Ctx.PORT_UP:
                pass
            elif mtype == Ctx.PORT_DOWN:
                pass
            else:
                handle_general(s, ctx, var, b)
            if s0 != ctx.state and ctx.state == Ctx.ESTAB:
                print("adjacency established with %s" % tomac(ctx.receiver_name))
                send_port_up(s, ctx)

if __name__ == '__main__':
    ctx = Ctx()
    if ctx is None:
        print("WTF!")
    client = gevent.socket.create_connection(ctx.config.server)
    handle(client)
