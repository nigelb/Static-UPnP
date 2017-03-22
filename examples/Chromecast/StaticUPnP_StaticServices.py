# static_upnp responds to upnp search requests with statically configures responses.
# Copyright (C) 2016  NigelB
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import socket

from dnslib import DNSQuestion, QTYPE

from chromecast_helpers import get_chromecast_uuid, get_date, get_chromecast_mdns_response, get_service_descriptor, \
    get_chromecast_friendly_name
from mDNS import StaticMDNDService
from static_upnp.static import StaticService


OK = """HTTP/1.1 200 OK
CACHE-CONTROL: max-age={max_age}
DATE: {date}
EXT:
LOCATION: http://{ip}:{port}/ssdp/device-desc.xml
OPT: "http://schemas.upnp.org/upnp/1/0/"; ns=01
01-NLS: 161d2e68-1dd2-11b2-9fd5-f9d9dc2ad10b
SERVER: Linux/3.8.13+, UPnP/1.0, Portable SDK for UPnP devices/1.6.18
X-User-Agent: redsonic
ST: {st}
USN: {usn}
BOOTID.UPNP.ORG: 4
CONFIGID.UPNP.ORG: 2


"""

NOTIFY = """NOTIFY * HTTP/1.1
HOST: 239.255.255.250:1900
CACHE-CONTROL: max-age=1800
LOCATION: http://{ip}:{port}/ssdp/device-desc.xml
NT: {st}
NTS: {nts}
OPT: "http://schemas.upnp.org/upnp/1/0/"; ns=01
01-NLS: 161d2e68-1dd2-11b2-9fd5-f9d9dc2ad10b
SERVER: Linux/3.8.13+, UPnP/1.0, Portable SDK for UPnP devices/1.6.18
X-User-Agent: redsonic
USN: {uuid}


"""

chromecast_ip = socket.gethostbyname_ex("Chromecast")[2][0]
chromecast_port = 8008

# "uuid": "02582d8a-4a1a-51bb-df1d-f72ba822a4df",
chromecast_service_descriptor = get_service_descriptor(chromecast_ip, chromecast_port)
chromecast_uuid = get_chromecast_uuid(chromecast_service_descriptor)
chromecast_friendly_name = get_chromecast_friendly_name(chromecast_service_descriptor)

services = [
    StaticService({
        "ip": chromecast_ip,
        "port": chromecast_port,
        "uuid": chromecast_uuid,
        "max_age": "1800",
        "date": get_date
    },  1024,
        OK=OK,
        NOTIFY=NOTIFY,
        services=[
            {
              "st": "upnp:rootdevice",
              "usn": "uuid:{uuid}::{st}"
            },
            {
              "st": "uuid:{uuid}",
              "usn": "uuid:{uuid}"
            },
            {
              "st": "urn:dial-multiscreen-org:device:dial:1",
              "usn": "uuid:{uuid}::{st}"
            },
            {
              "st": "urn:dial-multiscreen-org:service:dial:1",
              "usn": "uuid:{uuid}::{st}"
            },
        ])
]

mdns_services=[StaticMDNDService(
    response_generator=lambda query: get_chromecast_mdns_response(query, chromecast_ip, chromecast_uuid, chromecast_friendly_name),
    dns_question=DNSQuestion(qname="_googlecast._tcp.local", qtype=QTYPE.PTR, qclass=32769)
)]
