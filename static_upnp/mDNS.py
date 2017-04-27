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
from argparse import Namespace
from multiprocessing import Queue, Process, Value

import ctypes

try:
    import queue
except:
    import Queue as queue

import time

import os
import select

from dnslib import OPCODE

from static_upnp.upnp_reciever import register_worker_signal_handler

from static_upnp.util import drop_privileges, setup_sockets
import socket


class StaticMDNDService:
    logger = logging.getLogger("StaticMDNDService")

    def __init__(self, query_matcher=None, response_generator=None, dns_question=None):
        self.query_matcher = query_matcher
        self.response_generator = response_generator
        self.dns_question = dns_question

    def matches(self, query):
        if self.query_matcher is not None:
            return self.query_matcher(query)
        for question in query.questions:
            if question.qname == self.dns_question.qname:
                return True
        return False


class mDNSResponder:
    logger = logging.getLogger("mDNSResponder")

    def __init__(self, address='224.0.0.251', port=5353, buffer_size=4096, ttl=1, delivery_count=3, services=None):
        self.address = address
        self.port = port
        self.buffer_size = buffer_size
        self.ttl = ttl
        self.delivery_count = delivery_count
        self.services = services

    def drop_privileges(self, uid_name, gid_name):
        return drop_privileges(self, uid_name, gid_name)

    def setup_sockets(self):
        return setup_sockets(self)

    def start(self):
        import StaticUPnP_Settings
        permissions = Namespace(**StaticUPnP_Settings.permissions)
        print(permissions)
        if permissions.drop_permissions:
            self.drop_privileges(permissions.user, permissions.group)

        self.setup_sockets()
        self.running = Value(ctypes.c_int, 1)
        self.queue = Queue()
        self.reciever_thread = Process(target=self.socket_handler, args=(self.queue, self.running))
        self.reciever_thread.start()
        self.runner_thread = Process(target=self.run, args=(self.queue, self.running))
        self.runner_thread.start()

    def run(self, _queue, running):
        from dnslib import dns
        while running.value:
            try:
                record = _queue.get(block=False)
                if record is not None:
                    request = dns.DNSRecord.parse(record[0])
                    self.handle_request(record, request)

            except queue.Empty as error:
                try:
                    time.sleep(0.1)
                except KeyboardInterrupt as ki:
                    print("KeyboardInterrupt")
                    print(running.value)
                    time.sleep(1)
            except Exception as error:
                self.logger.exception("Error")
                # self.reciever_thread.join()

    def socket_handler(self, queue, running):
        self.logger = logging.getLogger("mDNSResponder.schedule_handler")
        self.logger.info("PID: %s" % os.getpid())
        register_worker_signal_handler(self.logger)
        socks = [self.sockets[x] for x in self.sockets.keys()]
        while running.value:
            try:
                ready = select.select([socks], [], [], 10)
                for sock in ready:
                    rec = sock.recvfrom(self.buffer_size, socket.MSG_DONTWAIT)
                    self.logger.log(0, rec)
                    queue.put(rec)
            except socket.error as se:
                pass
            except Exception as e:
                self.logger.exception("Message")
            except KeyboardInterrupt as ki:
                time.sleep(1)

        for sock in socks:
            sock.close()
        self.logger.warn("Socket Handler shutting down...")

    def shutdown(self):
        self.running.value = 0

        self.logger.info("Shutdown")
        self.logger.info("---------------------------")

    def join(self):
        self.reciever_thread.join()
        self.runner_thread.join()

    def handle_request(self, record, msg):
        from dnslib import dns
        self.logger.debug("%s: %s, from: %s", OPCODE.get(msg.header.get_opcode()),
                          [x.qname.__str__() for x in msg.questions], record[1])
        if dns.OPCODE.get(msg.header.get_opcode()) == 'QUERY':
            for sr in self.services:
                if sr.matches(msg):
                    self.logger.debug(msg)
                    msg = sr.response_generator(msg)
                    self.logger.debug(msg)
                    for ip in self.sockets:
                        sock = self.sockets[ip]
                        for i in range(self.delivery_count):
                            sock.sendto(msg.pack(), ("224.0.0.251", 5353))
