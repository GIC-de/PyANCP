"""ANCP Subscriber Tests

Copyright (C) 2017-2024, Christian Giese (GIC-de)
SPDX-License-Identifier: MIT
"""
from ancp.subscriber import *
import pytest


def test_access_loop_enc():
    tlv = access_loop_enc(DataLink.ETHERNET, Encap1.DOUBLE_TAGGED_ETHERNET,
                          Encap2.EOAAL5_LLC)
    assert tlv.val == 16975360


def test_subscriber_all_attributes():
    subscriber = Subscriber(
        aci="0.0.0.0 eth 0", ari="A.B.C", state=LineState.SHOWTIME,
        up=1024, down=2048, min_up=128, min_down=256,
        att_up=2040, att_down=4090, max_up=2048, max_down=4096,
        dsl_type=DslType.VDSL2, data_link=DataLink.ETHERNET,
        encap1=Encap1.UNTAGGED_ETHERNET, encap2=Encap2.EOAAL5_LLC_FCS
    )
    len, tlvs = subscriber.tlvs
    assert len == 3

    assert struct.unpack_from("!HHI", tlvs, 36)[2] == DslType.VDSL2
    assert struct.unpack_from("!HHI", tlvs, 52)[2] == LineState.SHOWTIME
    assert struct.unpack_from("!HHI", tlvs, 60)[2] == 1024      # up
    assert struct.unpack_from("!HHI", tlvs, 68)[2] == 2048      # down
    assert struct.unpack_from("!HHI", tlvs, 76)[2] == 128       # min_up
    assert struct.unpack_from("!HHI", tlvs, 84)[2] == 256       # min_down
    assert struct.unpack_from("!HHI", tlvs, 92)[2] == 2040      # att_up
    assert struct.unpack_from("!HHI", tlvs, 100)[2] == 4090     # att_down
    assert struct.unpack_from("!HHI", tlvs, 108)[2] == 2048     # max_up
    assert struct.unpack_from("!HHI", tlvs, 116)[2] == 4096     # max_down


def test_subscriber_aci():
    subscriber = Subscriber(aci="0.0.0.0 eth 0", up=1024, down=20148)
    len, tlvs = subscriber.tlvs
    values = struct.unpack_from("!HHccccccccccccc", tlvs, 0)
    assert values[0] == TlvType.ACI
    assert values[1] == 13
    aci = "".join([v.decode("utf-8") for v in values[2:]])
    assert aci == "0.0.0.0 eth 0"


def test_subscriber_aaci_bin():
    S1 = Subscriber(aci="0.0.0.0 eth 0", aaci_bin=128)
    len, tlvs = S1.tlvs
    assert struct.unpack_from("!HHI", tlvs, 20) == (6, 4, 128)

    S2 = Subscriber(aci="0.0.0.0 eth 0", aaci_bin=(128, 7))
    len, tlvs = S2.tlvs
    assert struct.unpack_from("!HHII", tlvs, 20) == (6, 8, 128, 7)


def test_subscriber_aaci_bin_exception():
    with pytest.raises(ValueError):
        S1 = Subscriber(aci="0.0.0.0 eth 0", aaci_bin="128")
    with pytest.raises(ValueError):
        S1 = Subscriber(aci="0.0.0.0 eth 0", aaci_bin=[128, 7])
    with pytest.raises(ValueError):
        S1 = Subscriber(aci="0.0.0.0 eth 0", aaci_bin=(128, "7"))
