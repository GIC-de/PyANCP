# PyANCP

+ fix issue where not that all bytes are sent to the ANCP neighbor
+ add support for draft-lihawi-ancp-protocol-access-extension-13

## 0.1.7

+ fix collections iterable issue in python 3.10
+ convert client address parameters to string
+ add Copyright and SPDX-License-Identifier

## 0.1.6

+ create sender_name based on argument source_address
    + source_address: 1.2.3.4 --> sender_name: 01:02:03:04:00:00
    + default sender_name: 01:02:03:04:05:06 if no source_address is given

## 0.1.5

+ add Access-Aggregation-Circuit-ID-ASCII TLV
+ add Access-Aggregation-Circuit-ID-Binary TLV

## 0.1.4

Initial implementation of PyANCP client library.
