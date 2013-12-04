"""
Example code from https://blogs.oracle.com/ksplice/entry/learning_by_doing_writing_your
"""

__author__ = 'Casey Stoessl'

import optparse
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
    while True:
        recv_socket, send_socket = create_sockets(ttl)
        recv_socket.bind(("", port))
        send_socket.sendto("", (dest_name, port))
        curr_addr = None
        curr_name = None
        try:
            # socket.recvfrom() gives back (data, address), but we
            # only care about the latter.
            _, curr_addr = recv_socket.recvfrom(512)
            curr_addr = curr_addr[0]  # address is given as tuple
            try:
                curr_name = socket.gethostbyaddr(curr_addr)[0]
            except socket.error:
                curr_name = curr_addr
        except socket.error:
            pass
        finally:
            send_socket.close()
            recv_socket.close()

        if curr_addr is not None:
            curr_host = "%s (%s)" % (curr_name, curr_addr)
        else:
            curr_host = "*"
        print "%d\t%s" % (ttl, curr_host)

        ttl += 1
        if curr_addr == dest_addr or ttl > max_hops:
            break

    return 0

if __name__ == "__main__":
    main("google.com", 33434, 30)