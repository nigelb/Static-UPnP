#!/usr/bin/env python
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
import grp
import socket

import os
import pwd

from argparse import Namespace


def drop_privileges(self, uid_name, gid_name):
    if os.getuid() != 0:
        # We're not root so, like, whatever dude
        self.logger.info("Not running as root. Cannot drop permissions.")
        return

    # Get the uid/gid from the name
    running_uid = pwd.getpwnam(uid_name).pw_uid
    running_gid = grp.getgrnam(gid_name).gr_gid

    # Remove group privileges
    os.setgroups([])

    # Try setting the new uid/gid
    os.setgid(running_gid)
    os.setuid(running_uid)

    # Ensure a very conservative umask
    old_umask = os.umask(0o077)
    self.logger.info("Changed permissions to: %s: %i, %s, %i"%(uid_name, running_uid, gid_name, running_gid))

def setup_sockets(self):
    self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)


    import StaticUPnP_Settings
    interface_config = Namespace(**StaticUPnP_Settings.interfaces)
    ip_addresses = StaticUPnP_Settings.ip_addresses
    if len(ip_addresses) == 0:
        import netifaces
        ifs = netifaces.interfaces()
        if len(interface_config.include) > 0:
            ifs = interface_config.include
        if len(interface_config.exclude) > 0:
            for iface in interface_config.exclude:
                ifs.remove(iface)

        for i in ifs:
            addrs = netifaces.ifaddresses(i)
            if netifaces.AF_INET in addrs:
                for addr in addrs[netifaces.AF_INET]:
                    ip_addresses.append(addr['addr'])
                    self.logger.info("Regestering multicast on %s: %s"%(i, addr['addr']))

    for ip in ip_addresses:
        self.logger.info("Regestering multicast for: %s"%(ip))
        mreq=socket.inet_aton(self.address)+socket.inet_aton(ip)
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)


    self.sock.bind(('', self.port))