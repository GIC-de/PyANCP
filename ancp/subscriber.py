"""ANCP
"""
from __future__ import print_function
from __future__ import unicode_literals
from ancp import packet
import struct
import logging

log = logging.getLogger("ancp")


class TLV(object):
    def __init__(self, t, val):
        self.t = t
        self.len = 0
        self.off = 0
        self.val = val
        if isinstance(val, int):
            # int
            self.len = 4
            self.off = 4
        elif isinstance(val, list):
            # sub tlvs
            for sub in val:
                self.len += 4 + sub.len
                self.off += 4 + sub.off
        else:
            # string
            self.len = len(val)
            padl = 4 - (self.len % 4)
            if(padl < 4):
                self.val = val + bytearray(padl)
            self.off = len(self.val)


def mktlvs(tlvs):
    blen = 0
    for i in tlvs:
        blen += 4 + i.off
    b = bytearray(blen)
    off = 0
    for i in tlvs:
        if isinstance(i.val, list):
            struct.pack_into("!HH", b, off, i.t, i.len)
            off += 4
            for s in i.val:
                if isinstance(s.val, int):
                    struct.pack_into("!HHI", b, off, s.t, s.len, s.val)
                else:
                    fmt = "!HH%ds" % s.len
                    struct.pack_into(fmt, b, off, s.t, s.len, str(s.val))
                off += 4 + s.off
        else:
            if isinstance(i.val, int):
                struct.pack_into("!HHI", b, off, i.t, i.len, i.val)
            else:
                fmt = "!HH%ds" % i.len
                struct.pack_into(fmt, b, off, i.t, i.len, str(i.val))
            off += 4 + i.off
    return b


def mkcircuitid_tlv(circuit_id):
    return TLV(0x0001, circuit_id)


def mkremoteid_tlv(remote_id):
    return TLV(0x0002, remote_id)


def mkline_tlv(sub_tlvs):
    return TLV(0x0004, sub_tlvs)


def mkdsltype_tlv(dsl_type):
    return TLV(0x0091, dsl_type)


def mklinestate_tlv(line_state):
    return TLV(0x008f, line_state)


class Subscriber(object):

    def __init__(self, aci, ari=None, up=0, down=0, state=packet.SHOWTIME):
        self.aci = aci
        self.ari = ari
        self.state = state
        self.up = up
        self.down = down
        self.dsl_type = packet.ADSL2P

    @property
    def tlvs(self):
        line_sub_tlvs = [mkdsltype_tlv(self.dsl_type)]
        line_sub_tlvs.append(mklinestate_tlv(self.state))

        tlvs = [mkcircuitid_tlv(self.aci), mkline_tlv(line_sub_tlvs)]
        return (len(tlvs), mktlvs(tlvs))
