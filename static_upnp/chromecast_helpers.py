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

from datetime import timedelta, datetime
import time

def get_service_descriptor(hostname, port):
    import requests
    print("http://{}:{}/ssdp/device-desc.xml".format(hostname, port))
    r = requests.get("http://{}:{}/ssdp/device-desc.xml".format(hostname, port))
    return r.content

def get_chromecast_uuid(service_descriptor):
    import xml.etree.ElementTree as ET
    root = ET.fromstring(service_descriptor)
    ns = {
        'cc': 'urn:schemas-upnp-org:device-1-0',
    }
    return root.find("./cc:device/cc:UDN", ns).text.split(":")[1]

def get_chromecast_friendly_name(service_descriptor):
    import xml.etree.ElementTree as ET
    root = ET.fromstring(service_descriptor)
    ns = {
        'cc': 'urn:schemas-upnp-org:device-1-0',
    }
    return root.find("./cc:device/cc:friendlyName", ns).text

def get_chromecast_mdns_response(query_data, chromecast_ip, chromecast_uuid, friendly_name):
    from dnslib import dns, RR, QTYPE, A, PTR, TXT, SRV
    # query_a = dns.DNSRecord.parse(query_data)
    query_a = query_data
    ans = query_a.reply(ra=0)
    ans.questions = []
    collapsed_uuid=chromecast_uuid.replace("-","")
    long_mdns_name = "Chromecast-%s._googlecast._tcp.local"%collapsed_uuid
    ans.add_answer(RR("_googlecast._tcp.local", QTYPE.PTR, rdata=PTR(long_mdns_name), ttl=120))
    ans.add_ar(RR(long_mdns_name, QTYPE.TXT, rdata=TXT(["id=%s"%collapsed_uuid, "rm=", "ve=05", "md=Chromecast", "ic=/setup/icon.png", "fn=%s"%friendly_name, "ca=4101", "st=0", "bs=FA8FCA630F87", "rs="]), ttl=4500, rclass=32769))
    ans.add_ar(RR(long_mdns_name, QTYPE.SRV, rdata=SRV(0, 0, 8009, "%s.local"%chromecast_uuid), rclass=32769,ttl=120))
    ans.add_ar(RR("%s.local"%chromecast_uuid, QTYPE.A, rdata=A(chromecast_ip),rclass=32769,ttl=120))
    return ans.pack()


def get_date():
    ts=datetime.now()+timedelta(seconds=time.timezone)
    return ts.strftime("%a, %d %b %Y %H:%M:%S GMT")