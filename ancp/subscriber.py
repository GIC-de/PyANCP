"""ANCP
"""
from __future__ import print_function
from __future__ import unicode_literals
import struct
import logging

__all__ = ["Subscriber"]

log = logging.getLogger("ancp")

# LINE STATE
SHOWTIME = 1
IDLE = 2
SILENT = 3

# DSL TYPE
ADSL = 1
ADSL2 = 2
ADSL2P = 3
VDSL1 = 4
VDSL2 = 5
SDL = 6
OTHER = 0

# TLV TYPE
ACI = 0x0001
ARI = 0x0002
LINE = 0x0004
TYPE = 0x0091
STATE = 0x008f
UP = 0x0081
DOWN = 0x0082


# HELPER FUNCTIONS AND CALSSES ------------------------------------------------

class TLV(object):
    def __init__(self, t, val):
        self.type = t   # type
        self.val = val  # value
        self.len = 0    # length
        self.off = 0    # offset (lenth + padding)
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
            padding = 4 - (self.len % 4)
            if(padding < 4):
                self.val = val + bytearray(padding)
            self.off = len(self.val)


def mktlvs(tlvs):
    blen = 0
    for t in tlvs:
        blen += 4 + t.off
    b = bytearray(blen)
    off = 0
    for t in tlvs:
        if isinstance(t.val, list):
            # sub tlvs
            struct.pack_into("!HH", b, off, t.type, t.len)
            off += 4
            for s in t.val:
                if isinstance(s.val, int):
                    struct.pack_into("!HHI", b, off, s.type, s.len, s.val)
                else:
                    fmt = "!HH%ds" % s.len
                    struct.pack_into(fmt, b, off, s.type, s.len, str(s.val))
                off += 4 + s.off
        else:
            # tlv
            if isinstance(t.val, int):
                # int
                struct.pack_into("!HHI", b, off, t.type, t.len, t.val)
            else:
                # string
                fmt = "!HH%ds" % t.len
                struct.pack_into(fmt, b, off, t.type, t.len, str(t.val))
            off += 4 + t.off
    return b


# ANCP SUBSCRIBER -------------------------------------------------------------

class Subscriber(object):
    def __init__(self, aci, ari=None, up=0, down=0, state=SHOWTIME):
        self.aci = aci
        self.ari = ari
        self.state = state
        self.up = up
        self.down = down
        self.dsl_type = ADSL2P

    @property
    def tlvs(self):
        line_sub_tlvs = [TLV(TYPE, self.dsl_type)]
        line_sub_tlvs.append(TLV(STATE, self.state))

        tlvs = [TLV(ACI, self.aci), TLV(LINE, line_sub_tlvs)]
        return (len(tlvs), mktlvs(tlvs))
