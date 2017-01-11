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
import grp
import logging
import pwd
import queue
import signal
import socket
import time
from argparse import Namespace
from multiprocessing import Queue, Process, Value

import os
import schedule
from collections import defaultdict



class AttributeDict(dict):
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__


def parse_search_request(request):
    data, sender = request
    if not (data.startswith(b"M-SEARCH") or data.startswith(b"NOTIFY")):
        return None
    http, headers = data.replace(b"\r", b"").split(b"\n", 1)
    method, path, version = http.split(b" ")
    result = AttributeDict(
            {
                "METHOD": method,
                "PATH": path,
                "VERSION": version,
                "HEADERS": defaultdict(list),
                "REMOTE": sender
            }
    )
    for line in headers.split(b"\n"):
        line = line.strip()
        if len(line) > 0:
            header, value = line.split(b":", 1)
            result.HEADERS[header].append(value.strip())
    return result


request_handlers = [parse_search_request]


def parse_request(request):
    for request_handler in request_handlers:
        result = request_handler(request)
        if result is not None:
            return result
    # print request
    return None


class UPnPServiceResponder:
    logger = logging.getLogger("UPnPServiceResponder")

    def __init__(self, address='239.255.255.250', port=1900, buffer_size=4096, services=None):

        self.address = address
        self.port = port
        self.buffer_size = buffer_size
        self.services = services

        self.setup_sockets()
        import StaticUPnP_Settings
        permissions = Namespace(**StaticUPnP_Settings.permissions)
        print(permissions)
        if permissions.drop_permissions:
            self.drop_privileges(permissions.user, permissions.group)

        self.running = Value(ctypes.c_int, 1)
        self.queue = Queue()
        self.reciever_thread = Process(target=self.socket_handler, args=(self.queue, self.running))
        self.reciever_thread.start()
        self.schedule_thread = Process(target=self.schedule_handler, args=(self.running,))
        self.schedule_thread.start()

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
            mreq=socket.inet_aton(self.address)+socket.inet_aton(ip)
            self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)


        self.sock.bind(('', self.port))


    def schedule_handler(self, running):
        self.logger = logging.getLogger("UPnPServiceResponder.schedule_handler")
        self.logger.info("PID: %s"%os.getpid())
        register_worker_signal_handler(self.logger)
        time.sleep(2)
        self.do_notify(b"ssdp:alive")
        sch = schedule.Scheduler()
        sch.every(300).seconds.do(lambda: self.do_notify(b"ssdp:alive"))

        while running.value:
            sch.run_pending()
            time.sleep(0.1)
        self.logger.warn("Scheduler shutting down...")

    def do_notify(self, nts):
        for service_descriptor in self.services:
            for service in service_descriptor.services:
                fmt = self.create_fmt(service_descriptor.params, service)
                fmt['nts'] = nts
                response_data = service_descriptor.NOTIFY.format(**fmt).replace("\n", "\r\n").encode("ascii")
                self.sock.sendto(response_data, (self.address, self.port))

    def socket_handler(self, queue, running):
        self.logger = logging.getLogger("UPnPServiceResponder.schedule_handler")
        self.logger.info("PID: %s"%os.getpid())
        register_worker_signal_handler(self.logger)
        sock = self.sock
        while running.value:
            try:
                rec = sock.recvfrom(self.buffer_size)
                self.logger.debug(rec)
                queue.put(rec)
            except Exception as e:
                self.logger.error(e)

        self.do_notify(b"ssdp:goodbye")
        self.sock.close()
        self.logger.warn("Socket Handler shutting down...")

    def run(self):
        while self.running.value:
            try:
                request = parse_request(self.queue.get(block=False))
                if request is None:
                    continue
                if request.METHOD == b"M-SEARCH": self.respond_ok(request)
            except queue.Empty as error:
                time.sleep(0.1)

        self.sock.close()

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
                for request_type in request.HEADERS[b'ST']:
                    if not request_type.startswith(b"ssdp:"):
                        if fmt['st'].encode("ascii") != request_type:
                            continue
                    response_data = service_descriptor.OK.format(**fmt).replace("\n", "\r\n").encode("ascii")
                    self.send(service_descriptor, response_data, request.REMOTE)

                    found = True
        if b'MX' in request: self.logger.debug(request.MX)
        self.logger.info("M-SEARCH for {}, Found: {}".format(request.HEADERS[b'ST'], found))


    def send(self, service_descriptor, response_data, REQUEST):
        self.sock.sendto(response_data, REQUEST)

    def shutdown(self):
        self.running.value = 0
        self.schedule_thread.join()
        self.reciever_thread.join()

        self.logger.info("Shutdown")
        self.logger.info("---------------------------")

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


class SpoofingUPnPServiceResponder(UPnPServiceResponder):
    def __init__(self, address='239.255.255.250', port=1900, buffer_size=4096, services=None, user="nobody",
                 group="nogroup", interface="eth0"):
        super().__init__(address, port, buffer_size, services)
        self.group = group
        self.user = user
        self.interface = interface
        self.drop_privileges(self.user, self.group)

    def setup_sockets(self):
        self.raw_sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)
        self.raw_sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW)
        self.raw_sock.bind((self.interface, 0))

    def send(self, service_descriptor, response_data, REQUEST):
        import ip, udp
        response_packet = udp.Packet(dport=REQUEST[1], sport=self.port, data=response_data)
        ip_packet = ip.Packet(
            dst=REQUEST[0],
            src=service_descriptor.params['ip'],
            data=udp.assemble(response_packet, 0),
            p=socket.IPPROTO_UDP,
            ttl=15

        )

        self.logger.debug(response_packet)
        data = udp.assemble(response_packet, 0)
        self.logger.debug(response_data)
        self.logger.debug(ip_packet)
        self.raw_sock.sendto(ip.assemble(ip_packet, 0), REQUEST.REMOTE)


def register_worker_signal_handler(logger):
    def signal_handler(signal, frame):
        logger.info("Ctrl+C Pressed...")
    signal.signal(signal.SIGINT, signal_handler)