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


def parse_tlvs(data):
    result = []
    offset = 0
    while offset < len(data):
        kind, length = struct.unpack_from("!HH", data, offset)
        value = data[offset + 4:offset + 4 + length]
        result.append((kind, value))
        offset += 4 + ((length + 3) // 4) * 4
    assert offset == len(data)
    return result


@pytest.mark.parametrize(
    "version,pon_type,first_rate",
    [("00", 0x0092, 0x0093), ("01", 0x0092, 0x0093),
     ("02", 0x1001, 0x1002)] +
    [("%02d" % version, 0x0097, 0x00b0) for version in range(3, 15)] +
    [("99", 0x0097, 0x00b0)],
)
def test_pon_subscriber_encodes_draft_specific_attributes(version, pon_type, first_rate):
    subscriber = PonSubscriber(
        aci="circuit", ari="remote", draft_version=version, pon_type=1,
        ont_onu_avg_down=1000, ont_onu_peak_down=2000,
        ont_onu_max_up=3000, ont_onu_ass_up=4000,
        pon_max_up=5000, pon_max_down=6000,
    )
    count, data = subscriber.tlvs
    outer = parse_tlvs(data)
    assert count == len(outer) == 3
    assert [(kind, value) for kind, value in outer[:2]] == [
        (0x0001, b"circuit"), (0x0002, b"remote")
    ]
    assert outer[2][0] == 0x0012
    assert [(kind, struct.unpack("!I", value)[0]) for kind, value in parse_tlvs(outer[2][1])] == [
        (pon_type, 1),
        (first_rate, 1000), (first_rate + 1, 2000),
        (first_rate + 2, 3000), (first_rate + 3, 4000),
        (first_rate + 4, 5000), (first_rate + 5, 6000),
    ]


def test_pon_subscriber_defaults_to_draft_01():
    _, data = PonSubscriber(aci="line", pon_type=1).tlvs
    assert parse_tlvs(parse_tlvs(data)[1][1])[0][0] == 0x0092


@pytest.mark.parametrize("version", [None, 4, "", "4", "-1", "100", "0a"])
def test_subscribers_reject_invalid_draft_version(version):
    with pytest.raises(ValueError, match="draft"):
        PonSubscriber(aci="line", draft_version=version)
    with pytest.raises(ValueError, match="draft"):
        Subscriber(aci="line", draft_version=version)


@pytest.mark.parametrize(
    "version,first_rate",
    [("00", 0x009b), ("01", 0x009b), ("02", 0x1008)] +
    [("%02d" % version, 0x009b) for version in range(3, 15)] +
    [("99", 0x009b)],
)
def test_dsl_subscriber_encodes_lihawi_throughput_extensions(version, first_rate):
    _, data = Subscriber(aci="line", draft_version=version, etr_up=100,
                         etr_down=200, attetr_up=300, attetr_down=400,
                         gdr_up=500, gdr_down=600, attgdr_up=700,
                         attgdr_down=800).tlvs
    attributes = parse_tlvs(parse_tlvs(data)[1][1])
    extensions = [(kind, struct.unpack("!I", value)[0]) for kind, value in attributes
                  if kind >= 0x009b]
    assert extensions == list(zip(range(first_rate, first_rate + 8), range(100, 900, 100)))


@pytest.mark.parametrize("value", [-1, 0x100000000, "100", True])
def test_lihawi_attributes_reject_invalid_wire_values(value):
    with pytest.raises(ValueError, match="unsigned 32-bit"):
        PonSubscriber(aci="line", ont_onu_max_up=value).tlvs
    with pytest.raises(ValueError, match="unsigned 32-bit"):
        Subscriber(aci="line", etr_up=value).tlvs


@pytest.mark.parametrize("value", [0, 0xffffffff])
def test_lihawi_attributes_accept_unsigned_wire_boundaries(value):
    _, pon_data = PonSubscriber(aci="line", draft_version="02",
                                ont_onu_max_up=value).tlvs
    pon_attributes = parse_tlvs(parse_tlvs(pon_data)[1][1])
    assert struct.unpack("!I", pon_attributes[1][1])[0] == value

    _, dsl_data = Subscriber(aci="line", draft_version="02", etr_up=value).tlvs
    dsl_attributes = parse_tlvs(parse_tlvs(dsl_data)[1][1])
    assert struct.unpack("!I", dsl_attributes[-1][1])[0] == value
