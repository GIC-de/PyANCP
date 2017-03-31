###################
ANCP Client Library
###################

The client library allows to setup and control sessions to an ANCP server.

Session Setup
-------------

Following an example of how to create an ANCP session.

.. code-block:: python

    from ancp.client import Client

    client = Client(address="1.2.3.4")
    client.connect()


.. warning:: IPv6 is currently not supported!

It is also possible to specify the source address and destination port (default 6068).
The default tech type is `DSL` which can be changed to `ANY` or `PON`. The argument
`timer` (default 25 seconds) specifies the interval of periodically adjacency
messages to monitor the session.

.. code-block:: python

    from ancp.client import Client
    from ancp.client import TechTypes

    client = Client(address="1.2.3.4", source_address="1.2.3.5", port=6068
                    tech_type=TechTypes.DSL, timer=25.0)
    client.connect()


The `connect` method creates a TCP session and starts a background thread which
responds to messages from the server and generates periodically adjacency
messages (`timer`).

Following an example which shows how to keep a session active
until `KeyboardInterrupt`.

.. code-block:: python

    try:
        while client.established.is_set():
            time.sleep(1)
    except KeyboardInterrupt:
        client.disconnect()

The `disconnect` method send an `ANCP RSTACK` message to the server, waits
up to 1 seconds for response and closes TCP session.


ANCP Subscriber
---------------

ANCP subscribers are requires to generate :ref:`Port Up/Down Messages`.

.. code-block:: python

    from ancp.subscriber import Subscriber

    S1 = Subscriber(aci="0.0.0.0 eth 1", up=1024, down=16000)

All supported line attributes are described in :ref:`ancp/subscriber.py`.
The argument `aci` is mandatory. Attributes can be updated (e.g. `S1.up=1000`)
or removed (e.g. `S1.up=None`).


Port Up/Down Messages
---------------------

It is possible to send multiple port up/down in a single TCP
message.

.. code-block:: python

    # create ancp subscribers
    S1 = Subscriber(aci="0.0.0.0 eth 1", up=1024, down=16000)
    S2 = Subscriber(aci="0.0.0.0 eth 2", up=2048, down=32000)
    S3 = Subscriber(aci="0.0.0.0 eth 3", up=2048, down=32000)

    # send single port up message
    client.port_up(S1)

    # send multiple port up in a single tcp message
    client.port_up([S2, S3])

The `port_down` method behaves similar to `port_up`.

It is also possible to update line attributes without sending a port down message.

.. code-block:: python

    # create ancp subscribers
    S1 = Subscriber(aci="0.0.0.0 eth 1", up=1024, down=16000)

    # send single port up message
    client.port_up(S1)

    # change line attributes and send port up
    S1.up=768
    S1.down=14000
    client.port_up(S1)

    # send port up again
    client.port_up(S1)
