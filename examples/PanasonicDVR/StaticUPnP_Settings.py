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
import logging

#If static_upnp has been started as root and drop_permissions is set to True, then
#static_upnp will change its running permissions to be user and group.
permissions = {
    'drop_permissions': True,
    'user': "nobody",
    'group': "nobody"
}

# Logging Configuration
logging = {
    'level': logging.DEBUG,
    'format': '%(asctime)-15s %(levelname)-7s %(name)s %(filename)s:%(funcName)s:%(lineno)d - %(message)s',
    'log_file': "/var/log/static_upnp.log",
    'maxBytes': 10*1024*1024,
    'backupCount': 5,
    'enableFileLog': True,
    'enableSTDERRLog': True
}

# By default all interfaces that have an AF_INET address will be registered with the multicast group.
# If the ip_addresses list has entries, then only these ips will be used and the interfaces are ignored.
# If the include list has entries then only these interface's address will be registered.
# If the exclude list had entries then these will be removed from the current list of interfaces and they will not be
#   registered.
ip_addresses = []
interfaces = {
    # "include": ["eth0"],
    "include": [],
    # "exclude": ["eth1"]
    "exclude": []
}
