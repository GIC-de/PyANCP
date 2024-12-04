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
    GFAST = 8           # G.fast
    VDSL2_Q = 9         # VDSL2 Annex Q
    SDSL_BOND = 10      # SDSL bonded
    VDSL2_BOND = 11     # VDSL2 bonded
    GFAST_BOND = 12     # G.fast bonded
    VDSL2_Q_BOND = 13   # VDSL2 Annex Q bonded


class PonType(object):
    "PON Access Types"
    GPON = 1
    XG_PON1 = 2
    TWDM_PON = 3
    XGS_PON = 4
    WDM_PIN = 5
    UNKNOWN = 7
    OTHER = 0


class TlvType(object):
    "TLV Types (https://www.iana.org/assignments/ancp/ancp.xhtml#tlv-types)"
    ACI = 0x0001                        # Access-Loop-Circuit-ID
    ARI = 0x0002                        # Access-Loop-Remote-ID
    AACI_ASCII = 0x0003                 # Access-Aggregation-Circuit-ID-ASCII
    LINE = 0x0004                       # DSL-Line-Attributes
    SERVICE_PROFILE = 0x0005            # Service-Profile-Name
    AACI_BIN = 0x0006                   # Access-Aggregation-Circuit-ID-Binary
    OAM_LOOPBACK_TEST_PARAM = 0x0007    # OAM-Loopback-Test-Parameters
    OPAQUE_DATA = 0x0008                # Opaque-Data
    OAM_LOOPBACK_TEST_RESPONSE= 0x0009  # OAM-Loopback-Test-Response-String
    COMMAND = 0x0011                    # Command
    PON = 0x0012                        # PON-Access-Line-Attributes
    MC_SERVICE_PROFILE = 0x0013         # Multicast-Service-Profile	
    BW_ALLOCATION = 0x0015              # Bandwidth-Allocation	
    BW_REQUEST = 0x0016                 # Bandwidth-Request	
    MC_SERVICE_PROFILE_NAME = 0x0018    # Multicast-Service-Profile-Name
    MC_FLOW = 0x0019                    # Multicast-Flow
    LIST_ACTION = 0x0021                # List-Action
    SEQ_NUMBER = 0x0022                 # Sequence-Number
    WHITE_LIST_CAC = 0x0024             # White-List-CAC
    MREPCTL_CAC = 0x0025                # MRepCtl-CAC
    UP = 0x0081                         # Actual-Net-Data-Rate-Upstream
    DOWN = 0x0082                       # Actual-Net-Data-Rate-Downstream
    MIN_UP = 0x0083                     # Minimum-Net-Data-Rate-Upstream
    MIN_DOWN = 0x0084                   # Minimum-Net-Data-Rate-Downstream
    ATT_UP = 0x0085                     # Attainable-Net-Data-Rate-Upstream
    ATT_DOWN = 0x0086                   # Attainable-Net-Data-Rate-Downstream
    MAX_UP = 0x0087                     # Maximum-Net-Data-Rate-Upstream
    MAX_DOWN = 0x0088                   # Maximum-Net-Data-Rate-Downstream
    MIN_NLPDR_UP = 0x0089               # Minimum-Net-Low-Power-Data-Rate-Upstream
    MIN_NLPDR_DOWN = 0x008a             # Minimum-Net-Low-Power-Data-Rate-Downstream
    MAX_INT_DELAY_UP = 0x008b           # Maximum-Interleaving-Delay-Upstream
    ACT_INT_DELAY_UP = 0x008c           # Actual-Interleaving-Delay-Upstream
    MAX_INT_DELAY_DOWN = 0x008d         # Maximum-Interleaving-Delay-Downstream
    ACT_INT_DELAY_DOWN = 0x008e         # Actual-Interleaving-Delay-Downstream
    STATE = 0x008f                      # DSL-Line-State
    ACC_LOOP_ENC = 0x0090               # Access-Loop-Encapsulation
    TYPE = 0x0091                       # DSL-Type
    REQ_SRC_IP = 0x0092                 # Request-Source-IP
    REQ_SRC_MAC = 0x0093                # Request-Source-MAC
    REP_BUF_TIME = 0x0094               # Report-Buffering-Time
    COM_BW = 0x0095                     # Committed-Bandwidth
    REQ_SRC_ID = 0x0096                 # Request-Source-Device-Id
    PON_TYPE = 0x0097                   # PON-Access-Type
    ETR_UP = 0x009b                     # Expected Throughput (ETR) upstream
    ETR_DOWN = 0x009c                   # Expected Throughput (ETR) downstream
    ATTETR_UP = 0x009d                  # Attainable Expected Throughput (ATTETR) upstream
    ATTETR_DOWN = 0x009e                # Attainable Expected Throughput (ATTETR) downstream
    GDR_UP = 0x009f                     # Gamma data rate (GDR) upstream
    GDR_DOWN = 0x00a0                   # Gamma data rate (GDR) downstream
    ATTGDR_UP = 0x00a1                  # Attainable Gamma data rate (ATTGDR) upstream
    ATTGDR_DOWN = 0x00a2                # Attainable Gamma data rate (ATTGDR) downstream
    ONT_ONU_AVG_DOWN = 0x00b0           # ONT/ONU-Average-Data-Rate-Downstream
    ONT_ONU_PEAK_DOWN = 0x00b1          # ONT/ONU-Peak-Data-Rate-Downstream
    ONT_ONU_MAX_UP = 0x00b2             # ONT/ONU-Maximum-Data-Rate-Upstream
    ONT_ONU_ASS_UP = 0x00b3             # ONT/ONU-Assured-Data-Rate-Upstream
    PON_MAX_UP = 0x00b4                 # PON-Tree-Maximum-Data-Rate-Upstream
    PON_MAX_DOWN = 0x00b5               # PON-Tree-Maximum-Data-Rate-Downstream
    STATUS_INFO = 0x0106                # Status-Info
    TARGET = 0x1000                     # Target (single access line variant)

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

    The parameters `dsl_type` and `pon_type` are exclusive.

    :param aci: Access-Loop-Circuit-ID
    :type aci: str
    :param ari: Access-Loop-Remote-ID
    :type ari: str
    :param aaci_bin: Access-Aggregation-Circuit-ID-Binary
    :type aaci_bin: int or tuple
    :param aaci_ascii: Access-Aggregation-Circuit-ID-ASCII
    :type aaci_ascii: str

    **DSL Line Attributes:**

    The following parameters are valid for DSL subscribers only.

    :param state: DSL-Line-State (default: SHOWTIME)
    :type state: ancp.subscriber.LineState
    :param up: Actual-Net-Data-Rate-Upstream (kbits/s)
    :type up: int
    :param down: Actual-Net-Data-Rate-Downstream (kbits/s)
    :type down: int
    :param min_up: Minimum-Net-Data-Rate-Upstream (kbits/s)
    :type min_up: int
    :param min_down: Minimum-Net-Data-Rate-Downstream (kbits/s)
    :type min_down: int
    :param att_up: Attainable-Net-Data-Rate-Upstream (kbits/s)
    :type att_up: int
    :param att_down: Attainable-Net-Data-Rate-Downstream (kbits/s)
    :type att_down: int
    :param max_up: Maximum-Net-Data-Rate-Upstream (kbits/s)
    :type max_up: int
    :param max_down: Maximum-Net-Data-Rate-Downstream (kbits/s)
    :type max_down: int
    :param dsl_type: DSL-Type (default: OTHER)
    :type dsl_type: ancp.subscriber.DslType
    :param data_link: Access-Loop-Encapsulation - Data Link (default: ETHERNET)
    :type data_link: ancp.subscriber.DataLink
    :param encap1: Access-Loop-Encapsulation - Encapsulation 1 (default: DOUBLE_TAGGED_ETHERNET)
    :type encap1: ancp.subscriber.Encap1
    :param encap2: Access-Loop-Encapsulation - Encapsulation 2 (default: EOAAL5_LLC)
    :type encap2: ancp.subscriber.Encap2

    **Additional DSL Line Attributes for G.Fast (draft-ietf-ancp-protocol-access-extension-06):**

    :param etr_up: Expected Throughput (ETR) upstream (kbits/s)
    :type etr_up: int
    :param etr_down: Expected Throughput (ETR) downstream (kbits/s)
    :type etr_down: int
    :param attetr_up: Attainable Expected Throughput (ATTETR) upstream (kbits/s)
    :type attetr_up: int
    :param attetr_down: Attainable Expected Throughput (ATTETR) downstream (kbits/s)
    :type attetr_down: int
    :param gdr_up: Gamma data rate (GDR) upstream (kbits/s)
    :type gdr_up: int
    :param gdr_down: Gamma data rate (GDR) downstream (kbits/s)
    :type gdr_down: int
    :param attgdr_up: Attainable Gamma data rate (ATTGDR) upstream (kbits/s)
    :type attgdr_up: int
    :param attgdr_down: Attainable Gamma data rate (ATTGDR) downstream (kbits/s)
    :type attgdr_down: int

    **PON Line Attributes (draft-lihawi-ancp-protocol-access-extension-13):**

    The following parameters are valid for PON subscribers only. The parameter
    `pon_type` must be set to create a PON subscriber.

    :param pon_type: PON-Access-Type
    :type pon_type: ancp.subscriber.PonType
    :param ont_onu_avg_down: ONT/ONU-Average-Data-Rate-Downstream (kbits/s)
    :type ont_onu_avg_down: int
    :param ont_onu_peak_down: ONT/ONU-Peak-Data-Rate-Downstream (kbits/s)
    :type ont_onu_peak_down: int
    :param ont_onu_max_up: ONT/ONU-Maximum-Data-Rate-Upstream (kbits/s)
    :type ont_onu_max_up: int
    :param ont_onu_ass_up: ONT/ONU-Assured-Data-Rate-Upstream (kbits/s)
    :type ont_onu_ass_up: int
    :param pon_max_up: PON-Tree-Maximum-Data-Rate-Upstream (kbits/s)
    :type pon_max_up: int
    :param pon_max_down: PON-Tree-Maximum-Data-Rate-Downstream (kbits/s)
    :type pon_max_down: int
    """
    def __init__(self, aci, **kwargs):
        self.aci = aci
        self.ari = kwargs.get("ari")
        self.aaci_bin = kwargs.get("aaci_bin")
        self.aaci_ascii = kwargs.get("aaci_ascii")
        self.pon_type = kwargs.get("pon_type")
        if self.pon_type:
            # PON LINE ATTRIBUTES
            self.ont_onu_avg_down = kwargs.get("ont_onu_ag_down")
            self.ont_onu_peak_down = kwargs.get("ont_onu_peak_down")
            self.ont_onu_max_up = kwargs.get("ont_onu_max_up")
            self.ont_onu_ass_up = kwargs.get("ont_onu_ass_up")
            self.pon_max_up = kwargs.get("pon_max_up")
            self.pon_max_down = kwargs.get("pon_max_down")
        else:
            # DSL LINE ATTRIBUTES
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
            # G.Fast attributes
            self.etr_up = kwargs.get("etr_up")
            self.etr_down = kwargs.get("etr_down")
            self.attetr_up = kwargs.get("attetr_up")
            self.attetr_down = kwargs.get("attetr_down")
            self.gdr_up = kwargs.get("gdr_up")
            self.gdr_down = kwargs.get("gdr_down")
            self.attgdr_up = kwargs.get("attgdr_up")
            self.attgdr_down = kwargs.get("attgdr_down")


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
        if self.pon_type is not None:
            # PON LINE ATTRIBUTES
            pon = [TLV(TlvType.PON_TYPE, self.pon_type)]
            if self.ont_onu_avg_down is not None:
                pon.append(TLV(TlvType.ONT_ONU_AVG_DOWN, self.ont_onu_avg_down))
            if self.ont_onu_peak_down is not None:
                pon.append(TLV(TlvType.ONT_ONU_PEAK_DOWN, self.ont_onu_peak_down))
            if self.ont_onu_max_up is not None:
                pon.append(TLV(TlvType.ONT_ONU_MAX_UP, self.ont_onu_max_up))
            if self.ont_onu_ass_up is not None:
                pon.append(TLV(TlvType.ONT_ONU_ASS_UP, self.ont_onu_ass_up))
            if self.pon_max_up is not None:
                pon.append(TLV(TlvType.PON_MAX_UP, self.pon_max_up))
            if self.pon_max_down is not None:
                pon.append(TLV(TlvType.PON_MAX_DOWN, self.pon_max_down))
            tlvs.append(TLV(TlvType.PON, pon))
        else:
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
            # G.Fast attributes
            if self.etr_up is not None:
                line.append(TLV(TlvType.ETR_UP, self.etr_up))
            if self.etr_down is not None:
                line.append(TLV(TlvType.ETR_DOWN, self.etr_down))
            if self.attetr_up is not None:
                line.append(TLV(TlvType.ATTETR_UP, self.attetr_up))
            if self.attetr_down is not None:
                line.append(TLV(TlvType.ATTETR_DOWN, self.attetr_down))
            if self.gdr_up is not None:
                line.append(TLV(TlvType.GDR_UP, self.gdr_up))
            if self.gdr_down is not None:
                line.append(TLV(TlvType.GDR_DOWN, self.gdr_down))
            if self.attgdr_up is not None:
                line.append(TLV(TlvType.ATTGDR_UP, self.attgdr_up))
            if self.attgdr_down is not None:
                line.append(TLV(TlvType.ATTGDR_DOWN, self.attgdr_down))
            tlvs.append(TLV(TlvType.LINE, line))
        return (len(tlvs), mktlvs(tlvs))
