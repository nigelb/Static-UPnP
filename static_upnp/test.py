# import socket
# import udp
#
# udp_packet = udp.Packet()
# udp_packet.sport = 1024;
# udp_packet.dport = 3024;
# udp_packet.data = "\xFF\xFF\xFF\xFFrcon \"test\" test\0"
# packet = udp.assemble(udp_packet, 0)
#
# sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# ret = sock.sendto(packet, ("127.0.0.1", 1900))
# print "sent %d bytes" % ret




# print """NOTIFY * HTTP/1.1
# HOST: 239.255.255.250:1900
# CACHE-CONTROL: max-age=1800
# LOCATION: http://{ip}:{port}/8CC1218F2AF2/Server0/ddd
# NT: urn:schemas-upnp-org:service:ConnectionManager:2
# NTS: ssdp:alive
# SERVER: Linux/4.0 UPnP/1.0 Panasonic-UPnP-MW/1.0
# USN: uuid:4D454930-0100-1000-8000-8CC1218F2AF2::urn:schemas-upnp-org:service:ConnectionManager:2
#
# """.replace("\n","\r\n").__repr__()

# import socket
#
# import struct
#
# from multiprocessing import Queue, Process
#
# def a(queue):
#     MCAST_GRP = '239.255.255.250'
#     MCAST_PORT = 1900
#
#     sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
#     sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#     sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
#     sock.bind(('', MCAST_PORT))
#
#     mreq = struct.pack('4sl', socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)
#     sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
#
#     while True:
#         data, addr = sock.recvfrom(4096)
#         print data, addr
#
# queue = Queue()
# thread = Process(target=a, args=(queue,))
# thread.start()
#
# while True:
#     print queue.get()


#create a raw socket
import socket

import sys

import os, pwd, grp

def drop_privileges(uid_name='nobody', gid_name='nogroup'):
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

try:
    # s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)
    # drop_privileges()
    # while True:
    #     pass
    print "{data}".format(data=lambda:"ddddd")
except socket.error , msg:
    print 'Socket could not be created. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
    sys.exit()