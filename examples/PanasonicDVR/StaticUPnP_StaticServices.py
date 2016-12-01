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
from static_upnp.static import StaticService

OK = """HTTP/1.1 200 OK
CACHE-CONTROL: max-age={max_age}
EXT:
LOCATION: http://{ip}:{port}/8CC1218F2AF2/Server0/ddd
SERVER: Linux/4.0 UPnP/1.0 Panasonic-UPnP-MW/1.0
OPT: "http://schemas.upnp.org/upnp/1/0/"; ns=01
ST: {st}
USN: {usn}


"""

NOTIFY = """NOTIFY * HTTP/1.1
HOST: 239.255.255.250:1900
CACHE-CONTROL: max-age=1800
LOCATION: http://{ip}:{port}/8CC1218F2AF2/Server0/ddd
NT: {st}
NTS: {nts}
SERVER: Linux/4.0 UPnP/1.0 Panasonic-UPnP-MW/1.0
USN: {uuid}


"""

services = [
    StaticService({
        "ip": "10.0.0.16",
        "port": 60606,
        "uuid": "4D454930-0100-1000-8000-8CC1218F2AF2",
        "max_age": "1800",
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
              "st": "urn:schemas-upnp-org:device:MediaServer:2",
              "usn": "uuid:{uuid}::{st}"
            },
            {
              "st": "urn:schemas-upnp-org:service:ContentDirectory:2",
              "usn": "uuid:{uuid}::{st}"
            },
            {
              "st": "urn:schemas-upnp-org:service:ConnectionManager:2",
              "usn": "uuid:{uuid}::{st}"
            },
        ])
]
