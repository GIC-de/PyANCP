"""ANCP Subscribers

Copyright (C) 2017-2024, Christian Giese (GIC-de)
SPDX-License-Identifier: MIT
"""
from __future__ import print_function
from __future__ import unicode_literals
from builtins import bytes
import struct
import logging

log = logging.getLogger(__name__)


class LineState(object):
    "Line States"
    SHOWTIME = 1
    IDLE = 2
    SILENT = 3


class DslType(object):
    "DSL Types"
    ADSL = 1
    ADSL2 = 2
    ADSL2P = 3
    VDSL1 = 4
    VDSL2 = 5
    SDSL = 6
    OTHER = 0


class TlvType(object):
    "TLV Types"
    ACI = 0x0001            # Access-Loop-Circuit-ID
    ARI = 0x0002            # Access-Loop-Remote-ID
    AACI_ASCII = 0x0003     # Access-Aggregation-Circuit-ID-ASCII
    LINE = 0x0004
    AACI_BIN = 0x0006       # Access-Aggregation-Circuit-ID-Binary
    UP = 0x0081
    DOWN = 0x0082
    MIN_UP = 0x0083
    MIN_DOWN = 0x0084
    ATT_UP = 0x0085
    ATT_DOWN = 0x0086
    MAX_UP = 0x0087
    MAX_DOWN = 0x0088
    STATE = 0x008f
    ACC_LOOP_ENC = 0x0090
    TYPE = 0x0091


# Access-Loop-Encapsulation
class DataLink(object):
    "Access-Loop-Encapsulation - Data Link"
    ATM_AAL5 = 0
    ETHERNET = 1


class Encap1(object):
    "Access-Loop-Encapsulation - Encapsulation 1"
    NA = 0
    UNTAGGED_ETHERNET = 1
    SINGLE_TAGGED_ETHERNET = 2
    DOUBLE_TAGGED_ETHERNET = 3


class Encap2(object):
    "Access-Loop-Encapsulation - Encapsulation 2"
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
    __slots__ = ('type', 'val', 'len', 'off')

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
        elif isinstance(val, tuple):
            # list of int (e.g. for AACI_BIN)
            self.len = len(val) * 4
            self.off = self.len
        else:
            # string
            self.len = len(val)
            padding = 4 - (self.len % 4)
            if(padding < 4):
                self.off = len(val) + padding
            else:
                self.off = self.len


def mktlvs(tlvs):
    blen = 0
    for t in tlvs:
        blen += 4 + t.off
    b = bytearray(blen)
    off = 0
    for t in tlvs:
        if isinstance(t.val, tuple):
            # list of int (e.g. for AACI_BIN)
            struct.pack_into("!HH", b, off, t.type, t.len)
            off += 4
            for i in t.val:
                struct.pack_into("!I", b, off, i)
                off += 4
        elif isinstance(t.val, list):
            # sub tlvs
            struct.pack_into("!HH", b, off, t.type, t.off)
            off += 4
            for s in t.val:
                if isinstance(s.val, int):
                    struct.pack_into("!HHI", b, off, s.type, s.len, s.val)
                else:
                    fmt = "!HH%ds" % s.len
                    struct.pack_into(fmt, b, off, s.type, s.len, bytes(s.val, encoding='utf-8'))
                off += 4 + s.off
        else:
            # tlv
            if isinstance(t.val, int):
                # int
                struct.pack_into("!HHI", b, off, t.type, t.len, t.val)
            elif isinstance(t.val, tuple):
                # list of int (e.g. for AACI_BIN)
                struct.pack_into("!HH", b, off, t.type, t.len)
                off += 4
                for i in t.val:
                    struct.pack_into("!I", b, off, i)
                    off += 4
            else:
                # string
                fmt = "!HH%ds" % t.len
                struct.pack_into(fmt, b, off, t.type, t.len, bytes(t.val, encoding='utf-8'))
            off += 4 + t.off
    return b


def access_loop_enc(data_link, encap1, encap2):
    """Create the Access Loop Tlv

    :param data_link: The Data link type
    :type data_link: ancp.subscriber.DataLink
    :param encap1: The first Encapsulation type
    :type encap1: ancp.subscriber.Encap1
    :param encap2: The second Encapsulation type
    :type encap2: ancp.subscriber.Encap2
    :rtype: TLV
    """
    tlv = TLV(TlvType.ACC_LOOP_ENC, 0)
    tlv.len = 3
    tlv.off = 4
    tlv.val = data_link << 24 | encap1 << 16 | encap2 << 8
    return tlv


# ANCP SUBSCRIBER -------------------------------------------------------------

class Subscriber(object):
    """ANCP Subscriber

    :param aci: Access-Loop-Circuit-ID
    :type aci: str
    :param ari: Access-Loop-Remote-ID
    :type ari: str
    :param aaci_bin: Access-Aggregation-Circuit-ID-Binary
    :type aaci_bin: int or tuple
    :param aaci_ascii: Access-Aggregation-Circuit-ID-ASCII
    :type aaci_ascii: str
    :param state: DSL-Line-State
    :type state: ancp.subscriber.LineState
    :param up: Actual-Net-Data-Rate-Upstream
    :type up: int
    :param down: Actual-Net-Data-Rate-Downstream
    :type down: int
    :param min_up: Minimum-Net-Data-Rate-Upstream
    :type min_up: int
    :param min_down: Minimum-Net-Data-Rate-Downstream
    :type min_down: int
    :param att_up: Attainable-Net-Data-Rate-Upstream
    :type att_up: int
    :param att_down: Attainable-Net-Data-Rate-Downstream
    :type att_down: int
    :param max_up: Maximum-Net-Data-Rate-Upstream
    :type max_up: int
    :param max_down: Maximum-Net-Data-Rate-Downstream
    :type max_down: int
    :param dsl_type: DSL-Type
    :type dsl_type: ancp.subscriber.DslType
    :param data_link: Access-Loop-Encapsulation - Data Link
    :type data_link: ancp.subscriber.DataLink
    :param encap1: Access-Loop-Encapsulation - Encapsulation 1
    :type encap1: ancp.subscriber.Encap1
    :param encap2: Access-Loop-Encapsulation - Encapsulation 2
    :type encap2: ancp.subscriber.Encap2
    """
    def __init__(self, aci, **kwargs):
        self.aci = aci
        self.ari = kwargs.get("ari")
        self.aaci_bin = kwargs.get("aaci_bin")
        self.aaci_ascii = kwargs.get("aaci_ascii")
        self.state = kwargs.get("state", LineState.SHOWTIME)
        self.up = kwargs.get("up", 0)
        self.down = kwargs.get("down", 0)
        self.min_up = kwargs.get("min_up")
        self.min_down = kwargs.get("min_down")
        self.att_up = kwargs.get("att_up")
        self.att_down = kwargs.get("att_down")
        self.max_up = kwargs.get("max_up")
        self.max_down = kwargs.get("max_down")
        self.dsl_type = kwargs.get("dsl_type", DslType.OTHER)
        self.data_link = kwargs.get("data_link", DataLink.ETHERNET)
        self.encap1 = kwargs.get("encap1", Encap1.DOUBLE_TAGGED_ETHERNET)
        self.encap2 = kwargs.get("encap2", Encap2.EOAAL5_LLC)

    def __repr__(self):
        return "Subscriber(%s)" % (self.aci)

    @property
    def aaci_bin(self):
        return self._aaci_bin

    @aaci_bin.setter
    def aaci_bin(self, value):
        if value is not None:
            if isinstance(value, tuple):
                for v in value:
                    if not isinstance(v, int):
                        raise ValueError("invalid value for aaci_bin")
            elif not isinstance(value, int):
                raise ValueError("invalid value for aaci_bin")
        self._aaci_bin = value

    @property
    def tlvs(self):
        tlvs = [TLV(TlvType.ACI, self.aci)]
        if self.ari is not None:
            tlvs.append(TLV(TlvType.ARI, self.ari))
        if self.aaci_bin is not None:
            tlvs.append(TLV(TlvType.AACI_BIN, self.aaci_bin))
        if self.aaci_ascii is not None:
            tlvs.append(TLV(TlvType.AACI_ASCII, self.aaci_ascii))
        # DSL LINE ATTRIBUTES
        line = [TLV(TlvType.TYPE, self.dsl_type)]
        line.append(access_loop_enc(self.data_link, self.encap1, self.encap2))
        line.append(TLV(TlvType.STATE, self.state))
        if self.up is not None:
            line.append(TLV(TlvType.UP, self.up))
        if self.down is not None:
            line.append(TLV(TlvType.DOWN, self.down))
        if self.min_up is not None:
            line.append(TLV(TlvType.MIN_UP, self.min_up))
        if self.min_down is not None:
            line.append(TLV(TlvType.MIN_DOWN, self.min_down))
        if self.att_up is not None:
            line.append(TLV(TlvType.ATT_UP, self.att_up))
        if self.att_down is not None:
            line.append(TLV(TlvType.ATT_DOWN, self.att_down))
        if self.max_up is not None:
            line.append(TLV(TlvType.MAX_UP, self.max_up))
        if self.max_down is not None:
            line.append(TLV(TlvType.MAX_DOWN, self.max_down))
        tlvs.append(TLV(TlvType.LINE, line))
        return (len(tlvs), mktlvs(tlvs))
