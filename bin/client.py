#!/usr/bin/env python
"""ANCP Client Example

Copyright 2017 Christian Giese <cgiese@juniper.net>
"""
from ancp.client import Client
from ancp.subscriber import Subscriber
import time
import logging
import sys

# setup logging to stdout
log = logging.getLogger()
log.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
handler.setFormatter(logging.Formatter('%(asctime)-15s [%(levelname)-8s] %(message)s'))
log.addHandler(handler)

# setup ancp session
client = Client(address="1.2.3.4")
if client.connect():
    # create ancp subscribers
    S1 = Subscriber(aci="0.0.0.0 eth 1", up=1024, down=16000)
    S2 = Subscriber(aci="0.0.0.0 eth 2", up=2048, down=32000)
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
