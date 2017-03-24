"""ANCP Client Tests

Copyright 2017 Christian Giese <cgiese@juniper.net>
"""
from ancp.client import *


def test_tomac():
    mac = tomac((1, 2, 3,  4, 5, 6))
    assert mac == "01:02:03:04:05:06"
