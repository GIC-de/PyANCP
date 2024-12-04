#!/usr/bin/env python
"""ANCP Client Example for PON extensions (draft-ietf-ancp-protocol-access-extension-06)

Copyright (C) 2017-2024, Christian Giese (GIC-de)
SPDX-License-Identifier: MIT
"""
from ancp.client import *
from ancp.subscriber import *
import time
import logging
import sys

# GPON PROFILE
GPON_1G = {
    "pon_type": PonType.GPON,
    "ont_onu_avg_down": 1000000,
    "ont_onu_peak_down": 1000000,
    "ont_onu_max_up": 1000000,
    "ont_onu_ass_up": 1000000,
    "pon_max_up": 1200000,
    "pon_max_down": 2400000,
}

# setup logging to stdout
log = logging.getLogger()
log.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
handler.setFormatter(logging.Formatter('%(asctime)-15s [%(levelname)-8s] %(message)s'))
log.addHandler(handler)


# setup ancp session
client = Client(address="172.30.138.10", tech_type=TechTypes.PON)
if client.connect():
    # create ancp subscribers
    S1 = Subscriber(aci="0.0.0.0 eth 1", **GPON_1G )
    S2 = Subscriber(aci="0.0.0.0 eth 2", **GPON_1G)

    # send port-up for ancp subscribers
    client.port_up([S1, S2])
    # keep session active
    try:
        while client.established.is_set():
            time.sleep(1)
    except KeyboardInterrupt:
        # send port-down for ancp subscribers
        client.port_down([S1, S2])
        client.disconnect()
