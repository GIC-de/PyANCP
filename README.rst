.. image:: https://github.com/GIC-de/PyANCP/actions/workflows/python-test.yml/badge.svg
    :target: https://github.com/GIC-de/PyANCP/actions/workflows/python-test.yml
.. image:: https://coveralls.io/repos/github/GIC-de/PyANCP/badge.svg?branch=master
    :target: https://coveralls.io/github/GIC-de/PyANCP?branch=master
.. image:: https://readthedocs.org/projects/pyancp/badge/?version=latest
    :target: http://pyancp.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status


PyANCP
======

Python ANCP (RFC 6320) client and library.
PyANCP requires Python 2.7 or later, or Python 3.2 or later.

State: **BETA**

ANCP Library Example
--------------------

.. code-block:: python

    from ancp.client import Client
    from ancp.subscriber import Subscriber

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


Author: Christian Giese and Wolfgang Beck

Contributors:
- Istvan Ruzman
