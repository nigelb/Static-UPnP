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

import unittest

from dnslib import dns, RR, QTYPE, A, PTR, TXT, SRV, DNSQuestion, binascii, DNSBuffer

from static_upnp.chromecast_helpers import get_chromecast_mdns_response_2018_03

class Chromecast_mdns_response_2018_03(unittest.TestCase):

    def runTest(self):
        request  = "0002000000030000000000002a5f2539453545374338463437393839353236433942434439354432343038344636463042323743354544045f7375620b5f676f6f676c6563617374045f746370056c6f63616c00000c0001095f3233333633374445c037000c0001c03c000c0001"
        response_1 = "0000840000000001000000032a5f2539453545374338463437393839353236433942434439354432343038344636463042323743354544045f7375620b5f676f6f676c6563617374045f746370056c6f63616c00000c00010000007800302d4368726f6d65636173742d30323538326438613461316135316262646631646637326261383232613464662d31c03cc05e001080010000119400bc2369643d30323538326438613461316135316262646631646637326261383232613464662363643d323638413942424531423635363035324145374438334135343142354331423403726d3d0576653d30350d6d643d4368726f6d65636173741269633d2f73657475702f69636f6e2e706e671b666e3d57696c6c7920576f6e6b61277320506f6f6c20486f7573650763613d343130310473743d310f62733d464138464341363330463837046e663d310a72733d596f7554756265c05e0021800100000078002d000000001f492430323538326438612d346131612d353162622d646631642d663732626138323261346466c04dc16800018001000000780004c0a82a38"
        response_2 = "000084000000000100000003095f3233333633374445045f7375620b5f676f6f676c6563617374045f746370056c6f63616c00000c00010000007800302d4368726f6d65636173742d30323538326438613461316135316262646631646637326261383232613464662d31c01bc03d001080010000119400bc2369643d30323538326438613461316135316262646631646637326261383232613464662363643d323638413942424531423635363035324145374438334135343142354331423403726d3d0576653d30350d6d643d4368726f6d65636173741269633d2f73657475702f69636f6e2e706e671b666e3d57696c6c7920576f6e6b61277320506f6f6c20486f7573650763613d343130310473743d310f62733d464138464341363330463837046e663d310a72733d596f7554756265c03d0021800100000078002d000000001f492430323538326438612d346131612d353162622d646631642d663732626138323261346466c02cc14700018001000000780004c0a82a38"
        response_3 = "0000840000000001000000030b5f676f6f676c6563617374045f746370056c6f63616c00000c00010000007800302d4368726f6d65636173742d30323538326438613461316135316262646631646637326261383232613464662d31c00cc02e001080010000119400bc2369643d30323538326438613461316135316262646631646637326261383232613464662363643d323638413942424531423635363035324145374438334135343142354331423403726d3d0576653d30350d6d643d4368726f6d65636173741269633d2f73657475702f69636f6e2e706e671b666e3d57696c6c7920576f6e6b61277320506f6f6c20486f7573650763613d343130310473743d310f62733d464138464341363330463837046e663d310a72733d596f7554756265c02e0021800100000078002d000000001f492430323538326438612d346131612d353162622d646631642d663732626138323261346466c01dc13800018001000000780004c0a82a38"

        packed_records = [response_1, response_2, response_3]
        test_ans = [dns.DNSRecord.parse(bytes.fromhex(response_1)), dns.DNSRecord.parse(bytes.fromhex(response_2)), dns.DNSRecord.parse(bytes.fromhex(response_3))]

        query_a = dns.DNSRecord.parse(bytes.fromhex(request))
        print(query_a)
        print()
        # results = get_chromecast_mdns_response_2018_03(query_a, "192.168.3.55", "02582d8a-4a1a-51bb-df1d-f72ba822a4df", "Willy Wonka's Pool House", "FA8FCA630F87")
        results = get_chromecast_mdns_response_2018_03(query_a, "192.168.42.56", "02582d8a-4a1a-51bb-df1d-f72ba822a4df", "Willy Wonka's Pool House", "FA8FCA630F87", "268A9BBE1B656052AE7D83A541B5C1B4", "YouTube", st=1)
        results[0].header.id=0
        results[1].header.id=0
        results[2].header.id=0
        packed_results = [binascii.hexlify((ans.pack())).decode("ascii") for ans in results]

        self.assertEquals(len(test_ans), len(results), "Incorrect number of query responses.")

        for index in range(len(test_ans)):
            tr = test_ans[index]
            gr = results[index]
            if(packed_results[index] != packed_records[index]):

                self.compare_a(tr, gr)
                self.assertTrue(tr.a == gr.a, "a field not equal")

                self.compare_ar(tr, gr)
                self.assertTrue(tr.ar == gr.ar, "ar field not equal")
                self.assertTrue(tr.auth == gr.auth, "auth field not equal")

                self.compare_header(tr, gr)
                self.assertTrue(tr.header == gr.header, "header field not equal")
                self.assertTrue(tr.q == gr.q, "q field not equal")

                self.compare_questions(tr, gr)
                self.assertTrue(tr.questions == gr.questions, "qestions field not equal")

                self.assertTrue(tr.rr == gr.rr, "rr field not equal")
                print(dir(tr.header))
                print("/////////////////////////////////////")
                print(test_ans[index])
                print("/////////////////////////////////////")
                print(results[index])
                print("/////////////////////////////////////")
            self.assertEquals(packed_records[index], packed_results[index], "mDNS Response Incorrect at index: %s"%index)

    def pack_item(self, item):
        buf=DNSBuffer()
        item.pack(buf)
        return buf.hex()

    def compare_packed(self, original, generated, msg):
        ob = DNSBuffer()
        gb = DNSBuffer()
        original.pack(ob)
        generated.pack(gb)
        self.assertEquals(ob.hex(), gb.hex(), msg)

    def compare_a(self, original, generated):
        original = original.a
        generated = generated.a
        self.compare_packed(original, generated, "Packed a fields do not match.")

    def compare_questions(self, original, generated):
        original = original.questions
        generated = generated.questions
        self.assertEquals(len(original), len(generated), "Question lists are different lengths.")
        self.compare_packed(original, generated, "Packed questions fields do not match.")


    def compare_ar(self, original, generated):
        original = original.ar
        generated = generated.ar
        self.assertEquals(len(original), len(generated), "ar lists different sizes")
        for index in range(len(original)):
            ol = original[index]

            gl = generated[index]
            if ol != gl:
                print (ol)
                print("++++++++++++++++++++++++++++++++")
                print (gl)

            # Code from RR.__eq__
            # Handle OPT specially as may be different types (RR/EDNS0)
            if ol.rtype == QTYPE.OPT and getattr(gl,"rtype",False) == QTYPE.OPT:
                attrs = ('rname','rclass','rtype','ttl','rdata')
            else:
                self.assertEquals(type(gl), type(ol), "ar record types are different")
                # List of attributes to compare when diffing (ignore ttl)
                attrs = ('rname','rclass','rtype','rdata')
                # return all([getattr(ol,x) == getattr(gl,x) for x in attrs])
            for attr in attrs:
                self.assertEquals(getattr(ol, attr), getattr(gl,attr), "Fields %s are not equal."%attr)

            self.assertTrue(original[0] == generated[0], "Item %s not equal"%index)
            for index in range(len(original)):
                self.compare_packed(original[index], generated[index], "Packed ar fields do not match.")

    def compare_header(self, original, generated):
        original = original.header
        generated = generated.header
        attrs = ('qr','aa','tc','rd','ra','opcode','rcode')
        for attr in attrs:
            self.assertEquals(getattr(original, attr), getattr(generated, attr), "Header field: %s is not the same."%attr)
        self.compare_packed(original, generated, "Packed header fields do not match.")