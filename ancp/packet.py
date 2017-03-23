from __future__ import print_function
from __future__ import unicode_literals

RFC = 50

#
# message types
#
ADJACENCY = 10
PORT_MANAGEMENT = 32
PORT_UP = 80
PORT_DOWN = 81
ADJACENCY_UPDATE = 85

#
# adjacency state
#
IDLE = 1
SYNSENT = 2
SYNRCVD = 3
ESTAB = 4

#
# adjacency message codes
#
SYN = 1
SYNACK = 2
ACK = 3
RSTACK = 4

#
# tech types
#
ANY = 0
PON = 1
DSL = 5

#
# result field
#
Ignore = 0x00
Nack = 0x01
AckAll = 0x02
Success = 0x03
Failure = 0x04

#
# result code
#
NoResult = 0x000


# capabilities
TOPO = 1
OAM = 4

SHOWTIME = 1
