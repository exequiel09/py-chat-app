# chatserver.py
#
# Copyright(c) Exequiel Ceasar Navarrete <esnavarrete1@up.edu.ph>
# Licensed under MIT
# Version 1.1.3

import os
import sys
sys.path.insert(0, os.path.abspath('..'))

import socket
import select
import threading
import re
from helpers import strip_uid

# TODO: callbacks should be implemented as event listener
class ChatServer:
  PORT = 9000
  HOST = ''
  SOCKET_DICT = {}
  RECV_BUFFER = 4096

  def setPort(self, port):
    self.PORT = port

  def setHost(self, host):
    self.HOST = host

  def invoke(self, callback=None):
    is_success = True

    self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
      self.server_socket.bind((self.HOST, self.PORT))
      self.server_socket.listen(10)

      # add server socket object to the list of readable connections
      self.SOCKET_DICT['cs_main_sckt'] = self.server_socket

      if callback != None:
        # invoke a callback supplied
        callback("Starting Server on port: " + str(self.PORT))

      self.stop_thread_evt = threading.Event()

      # invoke the run method
      threading.Thread(name="py-chat-server-thread", target=self.run, args=(self.stop_thread_evt, callback,)).start()
    except:
      is_success = False

    return is_success

  def run(self, stop_event, callback=None):
    sock_local_copy = self.SOCKET_DICT.copy()

    while(not stop_event.is_set()):
      try:
        # get the list sockets which are ready to be read through select
        # 4th arg, time_out  = 0 : poll and never block
        ready_to_read, ready_to_write, in_error = select.select(sock_local_copy.values(), [], [], 0)

        for sock in ready_to_read:
          # a new connection request recieved
          if sock == self.server_socket:
            sockfd, addr = self.server_socket.accept()

            sock_local_copy['tmp'] = sockfd

          # a message from a client, not a new connection
          else:
            # process data recieved from client,
            try:
              # receiving data from the socket.
              data = sock.recv(self.RECV_BUFFER)

              if data:
                # there is something in the socket
                # check if its an alias or not
                re_alias = re.search('ch_alias:(.+)', data)

                if re_alias:
                  chat_alias = re_alias.group(1)

                  # store the temporary socket back to the dictionary with the correct key
                  sock_local_copy[chat_alias] = sock_local_copy['tmp']

                  # remove the temporary socket
                  sock_local_copy.pop('tmp')

                  # get the peername
                  peername = sock_local_copy[chat_alias].getpeername()

                  if callback != None:
                    callback(strip_uid(chat_alias) + " on IP address " + peername[0] + " has connected to the server.")

                  self.broadcast(self.server_socket, sock, "[Server] " + strip_uid(chat_alias) + ' on IP address ' + peername[0] + ' has connected in the chat room')
                else:
                  for name, socket in sock_local_copy.iteritems():
                    # broadcast the message
                    if socket == sock:
                      self.broadcast(self.server_socket, sock, '[' + strip_uid(name) + '] ' + data)

              else:
                deep_sock_local_copy = sock_local_copy.copy()
                for_removal = []

                # to prevent a runtime exception we store the name of the sockets in a list
                # then iterate it later for removal. since looping the dictionary and removing items at the same time
                # throws a RuntimeError
                for name, socket in deep_sock_local_copy.iteritems():
                  # remove the socket that's broken
                  if socket == sock:
                    for_removal.append(name)

                # remove items that are subject for removal
                for item in for_removal:
                  socket_to_remove = deep_sock_local_copy.get(item)
                  peername = socket_to_remove.getpeername()

                  deep_sock_local_copy.pop(item)

                  if callback != None:
                    callback(strip_uid(item) + " on IP address " + peername[0] + " has disconnected from the server.")

                  self.broadcast(self.server_socket, socket_to_remove, "[Server] " + strip_uid(item) + " on IP address " + peername[0] + " has left the chat room.")

                sock_local_copy = deep_sock_local_copy

            # exception
            except:
              if callback != None:
                callback(strip_uid(name) + " has disconnected from the server.")

              self.broadcast(self.server_socket, sock, "%s has gone offline" % strip_uid(name))
              continue

        self.SOCKET_DICT = sock_local_copy

      except:
        stop_event.set()

  def broadcast(self, server_socket, sock, message):
    for name, socket in self.SOCKET_DICT.iteritems():
      # send the message only to peer
      if socket != server_socket and socket != sock :
        try:
          socket.send(message)
        except:
          # broken socket connection
          socket.close()

          # broken socket, remove it
          if socket in self.SOCKET_DICT:
            self.SOCKET_DICT.pop(name)

  def stop(self, callback=None):
    # prevent from throwing errors by checking if the server_socket attribute exists.
    if hasattr(self, 'server_socket'):
      # stop the thread
      if hasattr(self, 'stop_thread_evt'):
        self.stop_thread_evt.set()

      # close all sockets
      for name, socket in self.SOCKET_DICT.iteritems():
        socket.close()

      # empty out the socket dictionary
      self.SOCKET_DICT.clear()

      if hasattr(self, 'stop_thread_evt'):
        del self.stop_thread_evt

      del self.server_socket

      if callback != None:
        # invoke a callback supplied
        callback("Stopping server listening on port: " + str(self.PORT))


