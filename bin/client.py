#!/usr/bin/env python
"""ANCP Client Example

Copyright 2017 Christian Giese <cgiese@juniper.net>
"""
from ancp.client import Client
from ancp.subscriber import Subscriber
import time
import logging
import sys
import signal

# setup logging to stdout
log = logging.getLogger()
log.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
handler.setFormatter(logging.Formatter('%(asctime)-15s [%(levelname)-8s] %(message)s'))
log.addHandler(handler)

client = Client(address="172.30.138.10")
if client.connect():
    S1 = Subscriber(aci="0.0.0.0 eth 1", up=1024, down=16000)
    S2 = Subscriber(aci="0.0.0.0 eth 2", up=2048, down=32000)
    client.port_up(subscriber=S1)
    client.port_up(subscriber=S2)
    try:
        while client.established.is_set():
            time.sleep(1)
    except KeyboardInterrupt:
        client.disconnect()
