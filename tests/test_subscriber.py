"""ANCP Subscriber Tests

Copyright 2017 Christian Giese <cgiese@juniper.net>
"""
from ancp.subscriber import *


def test_access_loop_enc():
    tlv = access_loop_enc(ETHERNET, DOUBLE_TAGGED_ETHERNET, EOAAL5_LLC)
    assert tlv.val == 16975360


def test_subscriber_aci():
    subscriber = Subscriber(aci="0.0.0.0 eth 0", up=1024, down=20148)
    len, tlvs = subscriber.tlvs
    values = struct.unpack_from("!HHccccccccccccc", tlvs, 0)
    assert values[0] == ACI
    assert values[1] == 13
    aci = "".join([v.decode("utf-8") for v in values[2:]])
    assert aci == "0.0.0.0 eth 0"
