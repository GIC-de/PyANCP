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

client = Client(address="172.30.138.10")
client.connect()

time.sleep(2)
S1 = Subscriber(aci="0.0.0.0 eth 1")
S2 = Subscriber(aci="0.0.0.0 eth 2")
client.port_up(subscriber=S1)
client.port_up(subscriber=S2)
try:
    while True:
        time.sleep(100)
except KeyboardInterrupt:
    client.disconnect()
