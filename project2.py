"""
Example code from https://blogs.oracle.com/ksplice/entry/learning_by_doing_writing_your
"""

__author__ = 'Casey Stoessl'

import optparse
import time
import struct
import socket
import sys

icmp = socket.getprotobyname('icmp')
udp = socket.getprotobyname('udp')

def create_sockets(ttl):
    """
    Sets up sockets necessary for the traceroute.  We need a receiving
    socket and a sending socket.
    """
    recv_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp)
    send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, udp)
    send_socket.setsockopt(socket.SOL_IP, socket.IP_TTL, ttl)
    return recv_socket, send_socket

def main(dest_name, port, max_hops):
    dest_addr = socket.gethostbyname(dest_name)
    ttl = 1
    rtt = -1
    min_window = 0
    max_window = max_hops
    while True:
        if max_window - min_window <= 1:
            print
            return ttl, rtt
        ttl = (min_window + max_window) / 2
        recv_socket, send_socket = create_sockets(ttl)
        recv_socket.bind(("", port))
        recv_socket.settimeout(2)
        send_socket.sendto("", (dest_name, port))
        curr_addr = None
        curr_name = None
        type = -1
        code = -1
        try:
            # socket.recvfrom() gives back (data, address), but we
            # only care about the latter.
            send_time = time.time()
            data, curr_addr = recv_socket.recvfrom(512)
            rtt = time.time() - send_time
            icmp_header = data[20:22]
            type, code = struct.unpack('bb', icmp_header)
            if type == 3 and code == 3:
                max_window = ttl
            elif type == 11 and code == 0:
                min_window = ttl
            else:
                print "Type and code not recognized"
                return -1, -1
            curr_addr = curr_addr[0]  # address is given as tuple
            try:
                curr_name = socket.gethostbyaddr(curr_addr)[0]
            except socket.error:
                curr_name = curr_addr
        except socket.error: # Timeout, most likely
            min_window = ttl
        finally:
            send_socket.close()
            recv_socket.close()

        if curr_addr is not None:
            curr_host = "%s (%s)" % (curr_name, curr_addr)
        else:
            curr_host = "*"

        print "TTL: %d\t%s\tType: %d, Code: %d" % (ttl, curr_host, type, code)
        print "\tRTT: %r" % rtt

if __name__ == "__main__":
    port = 33434
    max_hops = 30

    sites = ['google.com']
    
    for site in sites:
        main(site, port, max_hops)
