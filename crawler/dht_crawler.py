'''
    ==== A simple DHT node crawler ===
This module will try to contact nodes in the DHT and query
random info hashes in order to get other nodes. This is a
simple script that could probably be optimized a lot.
'''

import string
import queue
import struct
import logging
import time
import hashlib
import random
import os
import socket

from bencode import bencode, bdecode


# Write to console, to be replaced with a logger maybe
def w2c(s):
  print(s)


# Convert an ip and port from ascii chars to proper strings :
def addr_to_string(addr):
  ip = addr[0]
  port = addr[1]
  ip =  ".".join(map(lambda x: str(ord(x)), ip))
  port = struct.unpack(">H", port)[0]
  return (ip, port)



class Node(object):
  def __init__(self, p, d, port, version=""):
    self._ip = p # need a series of 4 ascii chars !
    self._id = d #  need ascii chars here !
    self._p = port # need two ascii chars here !
    self._version = version
    self.last_seen = time.time()

  def __repr__(self):
    # For a complete ID :
    # return self.get_sip() + ":" + str(self.get_sport()) + "/" + self._id.encode("hex")
    # For a shorter ID :
    return self.get_sip()

  def get_compact_node_info(self):
    return self._id + self._ip + self._p

  def get_sip(self):
    return ".".join(map(lambda x: str(ord(x)), self._ip))

  def get_sid(self):
    return self._id.encode("hex")

  def get_sport(self):
    return struct.unpack(">H", self._p)[0]

  def get_addr(self):
    return (self.get_sip(), self.get_sport())

class StupidTable(object):
  def __init__(self):
    self._nodes = {}
    self._index = 0

  def add_node(self, d, node):
    self._nodes[d] = node

  def get_node(self, d):
    return self._nodes[d]

  def get_random_node(self):
    return self._nodes[random.choice(list(self._nodes.keys()))]

  def __len__(self):
    return len(self._nodes.keys())




class DHT():
#                   Simple DHT node
#   This is a simple DHT node, with very basic functionnality
#   The idea is to access the dfferent possibilities of sending
#   requests, all the functions of the type send_*.
#   This will spawn an entry in the _transactions dict of the
#   following form :
#       _transactions[tid]  =   [handler, ipaddr, port, req1, req2]
#   with :
#       tid     = transaction id
#       handler = the handler for the response
#       ipaddr  = ip address of the recipient
#       port    = port of the recipient
#       req1    = request sent by this server (transaction start)
#       req2    = answer to req1, sent by the recipient (transaction end)
#
#
#   For now, this node is not capable of handling different requests.
#
  def __init__(self, version, port, d, db_conn=None):
    self._id = d
    self._version = version
    self._db_conn = db_conn
    self._rt = StupidTable()
    self._break = False
    self._q = queue.Queue()
    self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    self._sock.settimeout(10)
    self._sock.bind(("0.0.0.0", port))
    self._transactions = {}

  def set_up_new_transaction(self):
    tid = os.urandom(5)
    while tid in self._transactions.keys():
      tid = os.urandom(5)
    self._transactions[tid] = []
    return tid



  # RANDOM FIND NODE
  # ---------------------------------------------------------------
  #
  # Send a find_node request to a random node in the
  # routing table, with a random target
  # Note : WON'T WORK WITH AN EMPTY ROUTING TABLE !
  def find_random(self):
    rand_target = os.urandom(20)
    n = self._rt.get_random_node()
    t = self.set_up_new_transaction()
    req = { "t" : t, "y" : b"q", "q" : b"find_node", "a" : { "id" : self._id, "target" : rand_target }}
    self._q.put([req, (n._ip, n._p)])
    self._transactions[t].append(self.find_random_handler)
    self._transactions[t].append(n._ip)
    self._transactions[t].append(n._p)
    w2c("Node " + str(n) + " is queried a find_node request for target " + rand_target.encode("hex"))
  #
  #
  def find_random_handler(self, req):
    w2c("Find_node query answered")
    n = req["r"]["nodes"]
    i = 0
    # Let's extract the nodes by pinging them
    while len(n) - i >= 26:
      self.ping(n[i+20:i+24], n[i+24:i+26])
      i += 26
  #
  #
  # ---------------------------------------------------------------



  # PING
  # ---------------------------------------------------------------
  #
  # Send a ping to an ip:port
  # This is usually the start of the recursion process
  #
  # A successfull ping will trigger a find_node, which will
  # trigger more pings for every node discovered !
  #
  #
  def ping(self, ip, port):
    t = self.set_up_new_transaction()
    req = {"t" : t, "y" : b"q", "q" : b"ping", "a" : { "id" : self._id }}
    self._q.put([req, (ip, port)])
    self._transactions[t].append(self.ping_handler)
    self._transactions[t].append(ip)
    self._transactions[t].append(port)
    # req1 will be added at the time of sending
    w2c("Sending out ping to : " + str(addr_to_string((ip, port))))
  #
  #
  #
  # The ping_handler adds the now validated node to
  # the routing list.
  def ping_handler(self, resp):
    ip = self._transactions[resp["t"]][1]
    port = self._transactions[resp["t"]][2]
    d = resp["r"]["id"]
    if "v" in resp:
      n = Node(ip, d, port, resp["v"])
    else:
      n = Node(ip, d, port)
    self._rt.add_node(d.encode("hex"), n)
    w2c(str(n) + " answered the ping !")
    self.find_random()
  #
  # ---------------------------------------------------------------

  def get_peers_handler(self, req, addr):
    # Dummy response for now
    tid = req["t"]
    info_hash = req["a"]["info_hash"]
    resp = {"t": tid, "y": b"r", "r": {"id": self._id, "token": b"dummy", "nodes": b""}}
    self._sock.sendto(bencode(resp), addr)

  def announce_peer_handler(self, req, addr):
    # Dummy response for now
    tid = req["t"]
    info_hash = req["a"]["info_hash"]
    if self._db_conn:
        c = self._db_conn.cursor()
        c.execute("INSERT OR IGNORE INTO seeds (info_hash) VALUES (?)", (info_hash.hex(),))
        self._db_conn.commit()
    resp = {"t": tid, "y": b"r", "r": {"id": self._id}}
    self._sock.sendto(bencode(resp), addr)

  def _network_thread(self, iterations=10):
    # The main I/O function, used by the thread
    it =  iterations
    while (not self._break) and it > 0:
      w2c("\n----- iterations left " + str(it) + " -----")
      w2c("      KNOWN NODES : " + str(len(self._rt)))
      it -= 1

      if len(self._rt) > 0:
          self.find_random()

      # If there is something in the queue, send it as a new transaction :
      # Note that we will alternate sending / receveiving
      if (not self._q.empty()):
        data, addr = self._q.get()
        addr = addr_to_string(addr)
        t = data["t"]
        self._transactions[t].append(data)
        w2c("Sending : " + str(data) + " to " + str(addr))
        self._sock.sendto(bencode(data), addr)

      # Then receive :
      try:
        req, c = self._sock.recvfrom(4096)
        req = bdecode(req)
        #w2c("Incoming message : " + str(req) + " from " + str(c))
        if req["y"] == "r":
          # Response
          # If it is a valid transaction ID, call the handler and store :
          if req["t"] in self._transactions.keys():
            self._transactions[req["t"]].append(req)
            self._transactions[req["t"]][0](req)
        elif req["y"] == "q":
          # Query
          if req["q"] == "get_peers":
            self.get_peers_handler(req, c)
          elif req["q"] == "announce_peer":
            self.announce_peer_handler(req, c)
          break
        elif req["y"] == "e":
          # Error
          break
        else:
          raise RuntimeError("Unknown KRPC message : " + str(req["y"]))
      except socket.timeout:
        pass




if __name__ == "__main__":
  d = DHT(port=54767, version="XN\00\00".encode('utf-8'), d=hashlib.sha1("This is a test !".encode('utf-8')).digest())
  d.ping("".join(map(lambda x: chr(int(x)), "67.215.242.139".split("."))), struct.pack(">H", 6881))
  d._network_thread(iterations=5)
