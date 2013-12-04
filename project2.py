"""
For a list of sites, finds the hop count, round trip time, and time to live.
Sample traceroute code from https://blogs.oracle.com/ksplice/entry/learning_by_doing_writing_your
"""

__author__ = 'Casey Stoessl'

import time
import struct
import socket

icmp = socket.getprotobyname('icmp')
udp = socket.getprotobyname('udp')

def create_sockets(ttl):
    """
    Sets up sockets necessary for the traceroute.
    We need a receiving socket and a sending socket.
    """
    recv_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp)
    send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, udp)
    send_socket.setsockopt(socket.SOL_IP, socket.IP_TTL, ttl)
    return recv_socket, send_socket

def main(dest_name, port, max_hops):
    """
    Uses binary search to find the TTL and RTT of a given host.
    Returns TTL, RTT tuple.
    """
    dest_addr = socket.gethostbyname(dest_name)
    ttl = 1
    rtt = -1
    rtt_good = -1
    min_window = 0
    max_window = max_hops
    while True:
        if max_window - min_window <= 1:
            #we've reached the end of the binary search
            print
            return max_window, rtt_good
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
            #start the rtt clock timer
            send_time = time.time()
            data, curr_addr = recv_socket.recvfrom(512)
            #close the rtt upon receival of the socket data
            rtt = time.time() - send_time
            #retrieve the type and code from the data
            icmp_header = data[20:22]
            type, code = struct.unpack('bb', icmp_header)
            if type == 3 and code == 3:
                #we've reached the destination, try decreasing ttl
                max_window = ttl
                rtt_good = rtt
            elif type == 11 and code == 0:
                #we failed to reach the destination, try increasing ttl
                min_window = ttl
            else:
                print "Type and code not recognized"
                return -1, -1
            curr_addr = curr_addr[0]
            try:
                #try to resolve the host name using the IP address
                curr_name = socket.gethostbyaddr(curr_addr)[0]
            except socket.error:
                curr_name = curr_addr
        except socket.error:
            #timeout, most likely
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
    file = open('output.csv', 'w')
    file.write('Site,TTL,RTT\n')    

    sites = ['google.com', 'linkedin.com', 'reddit.com',
             'youtube.com', 'conduit.com', 't-online.de',
             'xhamster.com', 'cnet.com', 'sohu.com',
             'mpnrs.com', 'nytimes.com', 'indeed.com']
    
    for site in sites:
        print "Trying site: %s" % site
        ttl, rtt = main(site, port, max_hops)
        print "Finished %s with TTL: %r and RTT: %r" % (site, ttl, rtt)
        print
        file.write("%s,%d,%r\n" % (site, ttl, rtt))
    file.close()
