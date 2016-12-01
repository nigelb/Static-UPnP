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

import ctypes
import socket

import grp
import os
import pwd
import schedule

import ip, udp
import time
import struct
from collections import defaultdict

from multiprocessing import Queue, Process, Value

import logging


class AttributeDict(dict):
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__


def parse_search_request(request):
    data, sender = request
    if not (data.startswith("M-SEARCH") or data.startswith("NOTIFY")):
        return None
    http, headers = data.replace("\r", "").split("\n", 1)
    method, path, version = http.split(" ")
    result = AttributeDict(
            {
                "METHOD": method,
                "PATH": path,
                "VERSION": version,
                "HEADERS": defaultdict(list),
                "REMOTE": sender
            }
    )
    for line in headers.split("\n"):
        line = line.strip()
        if len(line) > 0:
            header, value = line.split(":", 1)
            result.HEADERS[header].append(value.strip())
    return result


request_handlers = [parse_search_request]


def parse_request(request):
    for request_handler in request_handlers:
        result = request_handler(request)
        if result is not None:
            return result
    print request
    return None


class UPnPServiceResponder:
    logger = logging.getLogger("UPnPServiceResponder")

    def __init__(self, address='239.255.255.250', port=1900, buffer_size=4096, services=None, user="nobody",
                 group="nogroup"):
        self.user = user
        self.group = group
        self.address = address
        self.port = port
        self.buffer_size = buffer_size
        self.services = services

        # self.raw_sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)
        # self.raw_sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW)
        # self.raw_sock.bind(("tap4", 0))

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        self.sock.bind(('', self.port))
        self.drop_privileges(user, group)

        self.running = Value(ctypes.c_int, 1)
        self.queue = Queue()
        self.reciever_thread = Process(target=self.socket_handler, args=(self.queue, self.running))
        self.reciever_thread.start()
        self.schedule_thread = Process(target=self.schedule_handler, args=(self.running,))
        self.schedule_thread.start()

    def schedule_handler(self, running):
        time.sleep(2)
        self.do_notify("ssdp:alive")
        sch = schedule.Scheduler()
        sch.every(300).seconds.do(lambda: self.do_notify("ssdp:alive"))

        while running.value:
            sch.run_pending()
            time.sleep(0.1)

    def do_notify(self, nts):
        for service_descriptor in self.services:
            for service in service_descriptor.services:
                fmt = self.create_fmt(service_descriptor.params, service)
                fmt['nts'] = nts
                response_data = service_descriptor.NOTIFY.format(**fmt).replace("\n", "\r\n")
                self.sock.sendto(response_data, (self.address, self.port))

    def socket_handler(self, queue, running):
        sock = self.sock
        mreq = struct.pack('4sl', socket.inet_aton(self.address), socket.INADDR_ANY)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        while running.value:
            rec = sock.recvfrom(self.buffer_size)
            self.logger.debug(rec)
            queue.put(rec)

    def run(self):
        # self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)

        while self.running.value:
            request = parse_request(self.queue.get())
            if request is None: continue
            if request.METHOD == "M-SEARCH": self.respond_ok(request)

    def respond_ok(self, request):
        if self.services is not None:
            self.respond_ok_static(request)

    def create_fmt(self, params, service):
        fmt = {}

        for key in params:
            if hasattr(params[key], '__call__'):
                fmt[key] = params[key]()
            else:
                fmt[key] = params[key]

        for key in service:
            fmt[key] = service[key]

        for key in fmt:
            if type(fmt[key]) == str:
                fmt[key] = fmt[key].format(**fmt)

        return fmt

    def respond_ok_static(self, request):
        found = False
        for service_descriptor in self.services:
            for service in service_descriptor.services:
                fmt = self.create_fmt(service_descriptor.params, service)
                for request_type in request.HEADERS['ST']:
                    # print request_type == fmt['st'], request_type, fmt['st']
                    if not request_type.startswith("ssdp:"):
                        if fmt['st'] != request_type:
                            continue
                    # print "============================================="
                    response_data = service_descriptor.OK.format(**fmt).replace("\n", "\r\n")
                    response_packet = udp.Packet(dport=request.REMOTE[1], sport=self.port, data=response_data)
                    ip_packet = ip.Packet(
                            dst=request.REMOTE[0],
                            src=service_descriptor.params['ip'],
                            data=udp.assemble(response_packet, 0),
                            p=socket.IPPROTO_UDP,
                            ttl=15

                    )
                    # print sock.send(ip.assemble(ip_packet, 0))
                    # print response_packet
                    # data = udp.assemble(response_packet, 0)
                    # self.logger.debug(response_data)
                    self.logger.debug(ip_packet)
                    # self.raw_sock.sendto(ip.assemble(ip_packet, 0), request.REMOTE)
                    self.sock.sendto(response_data, request.REMOTE)

                    found = True
        if 'MX' in request: print request.MX
        self.logger.info("M-SEARCH for {}, Found: {}".format(request.HEADERS['ST'], found))

    def drop_privileges(self, uid_name, gid_name):
        if os.getuid() != 0:
            # We're not root so, like, whatever dude
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
        old_umask = os.umask(077)

    def shutdown(self):
        self.running.value = False
        self.schedule_thread.join()
        self.reciever_thread.join()
        self.do_notify("ssdp:goodbye")
        print "---------------------------"
