"""ANCP Subscribers

Copyright 2017 Christian Giese <cgiese@juniper.net>
"""
from __future__ import print_function
from __future__ import unicode_literals
import struct
import logging

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
MIN_UP = 0x0083
MIN_DOWN = 0x0084
ATT_UP = 0x0085
ATT_DOWN = 0x0086
MAX_UP = 0x0087
MAX_DOWN = 0x0088
ACC_LOOP_ENC = 0x0090

# Access-Loop-Encapsulation
# DATA LINK
ATM_AAL5 = 0
ETHERNET = 1
# ENCAPSULATION 1
NA = 0
UNTAGGED_ETHERNET = 1
SINGLE_TAGGED_ETHERNET = 2
DOUBLE_TAGGED_ETHERNET = 3
# ENCAPSULATION 2
PPPOA_LLC = 1
PPPOA_NULL = 2
IPOA_LLC = 3
IPOA_Null = 4
EOAAL5_LLC_FCS = 5
EOAAL5_LLC = 6
EOAAL5_NULL_FCS = 7
EOAAL5_NULL = 8


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


def access_loop_enc(data_link, encap1, encap2):
    tlv = TLV(ACC_LOOP_ENC, 0)
    tlv.len = 3
    tlv.off = 4
    tlv.val = data_link << 24 | encap1 << 16 | encap2 << 8
    return tlv


# ANCP SUBSCRIBER -------------------------------------------------------------

class Subscriber(object):
    def __init__(self, aci, **kwargs):
        self.aci = aci
        self.ari = kwargs.get("ari")
        self.state = kwargs.get("state", SHOWTIME)
        self.up = kwargs.get("up", 0)
        self.down = kwargs.get("down", 0)
        self.min_up = kwargs.get("min_up")
        self.min_down = kwargs.get("min_down")
        self.att_up = kwargs.get("att_up")
        self.att_down = kwargs.get("att_down")
        self.max_up = kwargs.get("max_up")
        self.max_down = kwargs.get("max_down")
        self.dsl_type = kwargs.get("dsl_type", OTHER)
        self.data_link = kwargs.get("data_link", ETHERNET)
        self.encap1 = kwargs.get("encap1", DOUBLE_TAGGED_ETHERNET)
        self.encap2 = kwargs.get("encap2", EOAAL5_LLC)

    @property
    def tlvs(self):
        tlvs = [TLV(ACI, self.aci)]
        if self.ari is not None:
            tlvs.append(TLV(ARI, self.ari))
        # DSL LINE ATTRIBUTES
        line = [TLV(TYPE, self.dsl_type)]
        line.append(TLV(STATE, self.state))
        line.append(TLV(UP, self.up))
        line.append(TLV(DOWN, self.down))
        if self.min_up is not None:
            line.append(TLV(MIN_UP, self.min_up))
        if self.min_down is not None:
            line.append(TLV(MIN_DOWN, self.min_down))
        if self.att_up is not None:
            line.append(TLV(ATT_UP, self.att_up))
        if self.att_down is not None:
            line.append(TLV(ATT_DOWN, self.att_down))
        if self.max_up is not None:
            line.append(TLV(MAX_UP, self.max_up))
        if self.max_down is not None:
            line.append(TLV(MAX_DOWN, self.max_down))
        line.append(access_loop_enc(self.data_link, self.encap1, self.encap2))
        tlvs.append(TLV(LINE, line))
        return (len(tlvs), mktlvs(tlvs))
