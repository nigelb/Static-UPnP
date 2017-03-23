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
import queue

import time

import os
import select

from static_upnp.upnp_reciever import register_worker_signal_handler

from static_upnp.util import drop_privileges, setup_sockets
import socket


class StaticMDNDService:
    def __init__(self, query_matcher=None, response_generator=None, dns_question=None):
        self.query_matcher = query_matcher
        self.response_generator = response_generator
        self.dns_question = dns_question

    def matches(self, query):
        if self.query_matcher is not None:
            return self.query_matcher(query)
        for question in query.questions:
            return (question.qname == self.dns_question.qname)


class mDNSResponder:
    logger = logging.getLogger("mDNSResponder")

    def __init__(self, address='224.0.0.251', port=5353, buffer_size=4096, services=None):
        self.address = address
        self.port = port
        self.buffer_size = buffer_size
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
        self.runner = Process(target=self.run, args=(self.queue, self.running))
        self.runner.start()

    def run(self, _queue, running):
        from dnslib import dns
        while running.value:
            try:
                record = _queue.get(block=False)
                if record is not None:
                    request = dns.DNSRecord.parse(record[0])
                    self.handle_request(record, request)


            except queue.Empty as error:
                time.sleep(0.1)
            except Exception as error:
                self.logger.error("Error", error)
        # self.reciever_thread.join()

    def socket_handler(self, queue, running):
        self.logger = logging.getLogger("mDNSResponder.schedule_handler")
        self.logger.info("PID: %s"%os.getpid())
        register_worker_signal_handler(self.logger)
        sock = self.sock
        while running.value:
            try:
                ready = select.select([sock], [], [], 10)
                if ready:
                    rec = sock.recvfrom(self.buffer_size, socket.MSG_DONTWAIT)
                    self.logger.debug(rec)
                    queue.put(rec)
            except socket.error as se:
                pass
            except Exception as e:
                self.logger.exception("Message")

        self.sock.close()
        self.logger.warn("Socket Handler shutting down...")

    def shutdown(self):
        self.running.value = 0

        self.logger.info("Shutdown")
        self.logger.info("---------------------------")

    def handle_request(self, record, msg):
        from dnslib import dns
        self.logger.debug(msg)
        self.logger.debug(msg.header.get_opcode())
        if dns.OPCODE.get(msg.header.get_opcode()) == 'QUERY':
            for sr in self.services:
                if sr.matches(msg):
                    print (record[1])
                    self.sock.sendto(sr.response_generator(msg), record[1])
                    # self.sock.sendto(sr.response_generator(msg), ("224.0.0.251", 5353))
