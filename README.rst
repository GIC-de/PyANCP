.. image:: https://github.com/GIC-de/PyANCP/actions/workflows/python-test.yml/badge.svg
    :target: https://github.com/GIC-de/PyANCP/actions/workflows/python-test.yml
.. image:: https://coveralls.io/repos/github/GIC-de/PyANCP/badge.svg?branch=master
    :target: https://coveralls.io/github/GIC-de/PyANCP?branch=master
.. image:: https://readthedocs.org/projects/pyancp/badge/?version=latest
    :target: http://pyancp.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status


PyANCP
======

After installing PyANCP, the bounded test client ``bin/ancp_test.py`` supports
DSL and PON. It requires Python 3.3 or later and can be run from the checkout
with ``PYTHONPATH=.``.
``--draft-version NN`` selects the
`draft-lihawi <https://datatracker.ietf.org/doc/draft-lihawi-ancp-protocol-access-extension/>`_
TLV numbering (default ``01``).
PON drafts ``00``-``01`` use type ``0x0092`` and rates ``0x0093``-``0x0098``;
``02`` uses ``0x1001`` and ``0x1002``-``0x1007``; ``03`` and later use
``0x0097`` and ``0x00b0``-``0x00b5``. DSL ETR/ATTETR/GDR/ATTGDR attributes use
``0x1008``-``0x100f`` for draft ``02`` and ``0x009b``-``0x00a2`` otherwise.
Published drafts through ``14`` were checked; later versions use the ``03``
numbering provisionally. Rates are in kbit/s.

``PonSubscriber`` accepts ``pon_type``, ``ont_onu_avg_down``,
``ont_onu_peak_down``, ``ont_onu_max_up``, ``ont_onu_ass_up``, ``pon_max_up``
and ``pon_max_down``. ``Subscriber`` accepts upstream and downstream keyword
arguments for ETR, ATTETR, GDR and ATTGDR.

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
- Stefan Lieberth