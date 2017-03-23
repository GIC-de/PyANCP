from ancp.subscriber import *


def test_access_loop_enc():
    tlv = access_loop_enc(ETHERNET, DOUBLE_TAGGED_ETHERNET, EOAAL5_LLC)
    assert tlv.val == 16975360
