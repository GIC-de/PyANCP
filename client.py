from ancp.client import Client
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
try:
    while True:
        time.sleep(100)
except KeyboardInterrupt:
    client.disconnect()
