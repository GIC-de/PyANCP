"""ANCP
"""
from __future__ import print_function
from __future__ import unicode_literals
from ancp import packet


class Subscriber(object):

    def __init__(self, aci, ari=None, up=0, down=0, state=packet.SHOWTIME):
        self.aci = aci
        self.ari = ari
        self.up = up
        self.down = down
