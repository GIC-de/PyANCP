#!/usr/bin/env python3
"""Send one ANCP Port Up, keep the adjacency open, and send Port Down."""

import argparse
import time

from ancp.client import Client, TechTypes
from ancp.subscriber import DslType, PonSubscriber, Subscriber, parse_draft_version


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", required=True, help="BNG ANCP IPv4 address")
    parser.add_argument("--source", required=True, help="access-node ANCP IPv4 address")
    parser.add_argument("--aci", required=True)
    parser.add_argument("--ari", required=True)
    parser.add_argument("--up", required=True, type=int, help="upstream rate in kbit/s")
    parser.add_argument("--down", required=True, type=int, help="downstream rate in kbit/s")
    parser.add_argument("--technology", choices=("dsl", "pon"), default="dsl")
    parser.add_argument("--draft-version", type=parse_draft_version, default="01", metavar="NN")
    parser.add_argument("--pon-type", type=int, default=1)
    parser.add_argument("--hold-seconds", type=int, default=65)
    args = parser.parse_args(argv)
    if args.hold_seconds <= 0 or not all(0 <= value <= 0xffffffff for value in (args.up, args.down, args.pon_type)):
        parser.error("hold time must be positive; rates and PON type must be unsigned 32-bit integers")

    if args.technology == "pon":
        subscriber = PonSubscriber(
            args.aci, ari=args.ari, draft_version=args.draft_version,
            pon_type=args.pon_type, ont_onu_max_up=args.up, ont_onu_avg_down=args.down,
        )
        technology = TechTypes.PON
    else:
        subscriber = Subscriber(args.aci, ari=args.ari, up=args.up, down=args.down,
                                dsl_type=DslType.VDSL2, draft_version=args.draft_version)
        technology = TechTypes.DSL

    client = Client(address=args.target, source_address=args.source, tech_type=technology)
    if not client.connect():
        client.disconnect()
        raise RuntimeError("ANCP adjacency was not established")
    try:
        client.port_up(subscriber)
        print("ANCP_ADJACENCY_ESTABLISHED_PORT_UP_SENT", flush=True)
        deadline = time.monotonic() + args.hold_seconds
        while time.monotonic() < deadline:
            if not client.established.is_set():
                raise RuntimeError("ANCP adjacency was lost")
            time.sleep(min(1, max(0, deadline - time.monotonic())))
    finally:
        try:
            if client.established.is_set():
                client.port_down(subscriber)
        finally:
            client.disconnect()
    print("ANCP_PORT_DOWN_SENT_DISCONNECTED", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
