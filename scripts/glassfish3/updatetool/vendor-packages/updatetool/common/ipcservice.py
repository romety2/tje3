# -*- coding: utf-8 -*-
#
# DO NOT ALTER OR REMOVE COPYRIGHT NOTICES OR THIS HEADER.
#
# Copyright (c) 2010 Oracle and/or its affiliates. All rights reserved.
#
# The contents of this file are subject to the terms of either the GNU
# General Public License Version 2 only ("GPL") or the Common Development
# and Distribution License("CDDL") (collectively, the "License").  You
# may not use this file except in compliance with the License.  You can
# obtain a copy of the License at
# https://glassfish.dev.java.net/public/CDDL+GPL_1_1.html
# or packager/legal/LICENSE.txt.  See the License for the specific
# language governing permissions and limitations under the License.
#
# When distributing the software, include this License Header Notice in each
# file and include the License file at glassfish/bootstrap/legal/LICENSE.txt.
#
# GPL Classpath Exception:
# Oracle designates this particular file as subject to the "Classpath"
# exception as provided by Oracle in the GPL Version 2 section of the License
# file that accompanied this code.
#
# Modifications:
# If applicable, add the following below the License Header, with the fields
# enclosed by brackets [] replaced by your own identifying information:
# "Portions Copyright [year] [name of copyright owner]"
#
# Contributor(s):
# If you wish your version of this file to be governed by only the CDDL or
# only the GPL Version 2, indicate your decision by adding "[Contributor]
# elects to include this software in this distribution under the [CDDL or GPL
# Version 2] license."  If you don't indicate a single choice of license, a
# recipient has the option to distribute your version of this file under
# either the CDDL, the GPL Version 2 or to extend the choice of license to
# its licensees as provided above.  However, if you add GPL Version 2 code
# and therefore, elected the GPL Version 2 license, then the option applies
# only if the new code is made subject to such option by the copyright
# holder.
#

import wx
import threading
import sys
import os
import random
import socket
import atexit

import utils

_debug = False

CMD_LIST = ('APPLY_UPDATES', 'CHECK_UPDATES', 'GOODBYE', 'HELLO',
            'SHOW_UPDATES', 'SHOW', 'LOAD_CONFIG', 'RESTART', 'RESTART_CHECK',
            'SHUTDOWN', 'PROTOCOL_VERSION', 'EXIT_THREAD')

# Version 1.1 added PROTOCOL_VERSION and SHUTDOWN ops
# Version 1.2 added RESTART_CHECK
PROTOCOL_VERSION = '1.2'

class IPCServiceThread(threading.Thread):
    """
    This thread listends for connection attempts from other updatetools or
    notifiers.  It processes only one connection at a time.
    """
    def __init__(self, action_object, lock_type):
        threading.Thread.__init__(self)

        self.action_object = action_object
        self.lock_type = lock_type
        self.sock = None
        self.keep_thread_alive = True

        atexit.register(self._ipcservice_atexit_func)

    def run(self):

        # Find an available port, open a socket for listening
        port, self.sock = _get_port_socket()
        if self.sock is None: return

        # Store the host and port in the lock file
        if _set_lock_host_port(self.lock_type, port) == False:
            self.sock.close()
            return

        # Start listening for connections
        try:
            while self.keep_thread_alive:
                if _debug: print >> sys.stderr, "Waiting for connection..."

                # This overrides any global default setting.
                self.sock.settimeout(None)

                cxn_socket, dummy_addr = self.sock.accept()

                # The processing of the cxn could happen in another thread
                # to allow other cxns to be made at the same time.  But the
                # GUI is not prepared to handle this.  So we let the other
                # cxn attempts queue up and handle them on a first come first
                # serve basis.

                try:
                    while True:
                        command = cxn_socket.recv(8192)

                        if _debug: print >> sys.stderr, "Recv << : ", command

                        if not command: break

                        if not self.process_command(cxn_socket, command): break
                finally:
                    cxn_socket.close()
        finally:
            self.close_sock()


    def close_sock(self):

        _remove_lock_file(self.lock_type)

        if self.sock is None: return

        if _debug: print >> sys.stderr, "IPC: close_sock()"

        self.sock.close()
        self.keep_thread_alive = False
        self.sock = None

        return


    def process_command(self, cxn_socket, command):

        if command not in CMD_LIST: return False

        if command == 'HELLO':
            if _debug: print >> sys.stderr, "Process: HELLO"
            cxn_socket.sendall('OK')
            return True
        elif command == 'GOODBYE':
            if _debug: print >> sys.stderr, "Process: GOODBYE"
            cxn_socket.sendall('OK')
            return False
        elif command == 'EXIT_THREAD':
            if _debug: print >> sys.stderr, "Process: EXIT_THREAD"
            self.keep_thread_alive = False
            cxn_socket.sendall('OK')
            return False
        elif command == 'CHECK_UPDATES':
            if _debug: print >> sys.stderr, "Process: CHECK_UPDATES"
            func = getattr(self.action_object,
                                    "check_updates_without_notification", None)
            if callable(func):
                wx.CallAfter(func)
            cxn_socket.sendall('OK')
            return True
        elif command == 'LOAD_CONFIG':
            if _debug: print >> sys.stderr, "Process: LOAD_CONFIG"
            func = getattr(self.action_object, "reload_config", None)
            if callable(func):
                wx.CallAfter(func)
            cxn_socket.sendall('OK')
            return True
        elif command == 'APPLY_UPDATES':
            if _debug: print >> sys.stderr, "Process: APPLY_UPDATES"
            func = getattr(self.action_object, "notifier_apply_updates", None)
            if callable(func):
                wx.CallAfter(func)
            cxn_socket.sendall('OK')
            return True
        elif command == 'RESTART':
            if _debug: print >> sys.stderr, "Process: RESTART"
            func = getattr(self.action_object, "restart", None)
            if callable(func):
                wx.CallAfter(func)
            cxn_socket.sendall('OK')
            return True
        elif command == 'RESTART_CHECK':
            if _debug: print >> sys.stderr, "Process: RESTART_CHECK"
            func = getattr(self.action_object, "restart_if_needed", None)
            if callable(func):
                wx.CallAfter(func)
            cxn_socket.sendall('OK')
            return True
        elif command == 'SHOW_UPDATES':
            if _debug: print >> sys.stderr, "Process: SHOW_UPDATES"
            func = getattr(self.action_object, "notifier_show_updates", None)
            if callable(func):
                wx.CallAfter(func)
            cxn_socket.sendall('OK')
            return True
        elif command == 'SHOW':
            if _debug: print >> sys.stderr, "Process: SHOW"
            func = getattr(self.action_object, "raise_frame", None)
            if callable(func):
                wx.CallAfter(func)
            cxn_socket.sendall('OK')
            return True
        elif command == 'SHUTDOWN':
            if _debug: print >> sys.stderr, "Process: SHUTDOWN"
            func = getattr(self.action_object, "ipc_shutdown", None)
            if callable(func):
                wx.CallAfter(func)
            wx.CallAfter(self.action_object.ipc_shutdown)
            cxn_socket.sendall('OK')
            self.keep_thread_alive = False
            return True
        elif command == 'PROTOCOL_VERSION':
            if _debug: print >> sys.stderr, "Process: PROTOCOL_VERSION"
            cxn_socket.sendall(PROTOCOL_VERSION)
            cxn_socket.sendall('OK')
            return True
        else:
            # Unknown command
            if _debug: print >> sys.stderr, "Process: unknown command"
            return False


    def _ipcservice_atexit_func(self):
        if _debug: print >> sys.stderr, "Removing lock file."
        _remove_lock_file(self.lock_type)


def _get_hostname():

    try:
        # We don't know what encoding the hostname is in.  We guess that
        # it is latin-1 and if it is not we ignore those characters that
        # we can't use.
        hostname = unicode(socket.gethostname(), "latin-1", errors='ignore')
        if hostname == "":
            hostname = "logs"
        return socket.gethostbyaddr(hostname)[0]
    except socket.error:
        return "localhost"


# If the lock file exists load the host and port (host:port) from the file.
# returns host, port.
def _get_lock_host_port(lock_type):

    # Issue #961
    if wx.Platform == "__WXMAC__" and not wx.App.IsDisplayAvailable():  
        lock_file = os.path.join(os.path.expanduser("~"), 
                                 "Library/Application Support",
                                 "updatetool", "lock",
                                 lock_type + "-" + _get_hostname())
    else:
        lock_file = os.path.join(utils.get_config_dir(), 
                                 "lock", lock_type + "-" + _get_hostname())

    if _debug: print >> sys.stderr, "Lock path: ", lock_file

    if os.path.exists(lock_file):
        try:
            f = open(lock_file, "r")
            line = f.readline().rstrip()
            f.close()
        except IOError, e:
            if _debug: print >> sys.stderr, "IO Error reading the lock file:", e
            return "", 0

        if not len(line): return "", 0

        if _debug: print >> sys.stderr, "Lock file contains: ", line

        host_port = line.split(':')

        host = host_port[0]

        try:
            port = int(host_port[1])
        except ValueError, e:
            if _debug: print >> sys.stderr, "Lock file ValueError: "
            return "", 0

        return host, port

    return "", 0


def _set_lock_host_port(lock_type, port):

    lock_file = os.path.join(utils.get_config_dir(), "lock",
                                              lock_type + "-" + _get_hostname())

    if not _create_lock_directory(): return False

    try:
        f = open(lock_file, "w")
        f.write(_get_hostname() + ":" + str(port) + "\n")
        f.close()
    except IOError, e:
        if _debug: print >> sys.stderr, "Could not open/write lock file: ", e
        return False

    return True


def _create_lock_directory():

    lock_dir = os.path.join(utils.get_config_dir(), "lock")

    # Create the lock dir if it does not exist
    if os.path.exists(lock_dir):
        if not os.path.isdir(lock_dir):
            if _debug: print >> sys.stderr, "Lock dir not a directory: ", \
                                                              lock_dir
            return False
    else:
        try:
            os.makedirs(lock_dir)
        except:
            if _debug: print >> sys.stderr, "Couldn't create lock dir: ", \
                                                              lock_dir
            return False

    if _debug: print >> sys.stderr, "Lock dir created: ", lock_dir

    return True


def _remove_lock_file(lock_type):

    lock_file = os.path.join(utils.get_config_dir(), "lock",
                                              lock_type + "-" + _get_hostname())

    if not os.path.exists(lock_file): 
        return

    try:
        os.remove(lock_file)
    except Exception, e:
        if _debug: print >> sys.stderr, "Could not remove lock file: ", e
        return 

    return


# Return true if it sucessfully contacts another instance
def process_running(lock_type, show=False, action=None):

    sock = _create_sock(lock_type)

    if sock is None:
        return False

    # XXX: If the server is stopped (e.g. ctrl-Z) it will not respond
    # XXX: Need to set a timeout.
    if _send_command(sock, "HELLO") != "OK":
        sock.close()
        return False

    # If indicated send the GUI a SHOW command.
    if show:
        if _send_command(sock, "SHOW") != "OK":
            sock.close()
            return False

    # If indicated send the GUI a LIST/APPLY command.
    if action in ("SHOW_UPDATES", "APPLY_UPDATES"):
        if _send_command(sock, action) != "OK":
            sock.close()
            return False

    if _send_command(sock, "GOODBYE") != "OK":
        sock.close()
        return False

    sock.close()
    return True


def _create_sock(lock_type):

    host, port = _get_lock_host_port(lock_type)

    if host == "" or port == 0:
        return None

    # We ignore the host for now.  In the future it may be utilized.
    # We only connect to the tool running on the local host.
    sock = _get_socket("127.0.0.1", port)

    # We couldn't open the socket.
    if sock is None:
        if _debug: print >> sys.stderr, "Couldn't open the port: ", port
        return None

    if _debug: print >> sys.stderr, "Using port: ", port

    return sock


def send_command(lock_type, command):

    sock = _create_sock(lock_type)

    if sock is None: return False

    if _send_command(sock, command) != 'OK':
        # The GUI may not be running
        sock.close()
        return False

    # If the command is a RESTART/SHUTDOWN we don't send a GOODBYE because
    # the tool may restart before the GOODBYE/SHUTDOWN is received.
    if command != 'RESTART' and command != 'SHUTDOWN':
        if _send_command(sock, "GOODBYE") != 'OK':
            # The GUI may not be running
            sock.close()
            return False

    sock.close()
    return True


def _send_command(sock, cmd):

    if _debug: print >> sys.stderr, "Send >> : ", cmd

    if cmd not in CMD_LIST: return ""

    try:
        sock.sendall(cmd)
    except socket.error, cmd:
        return ""

    sock.settimeout(2.0)

    try:
        response = sock.recv(8196)
    except socket.error, cmd:
        if _debug: print >> sys.stderr, "Recv << : TIMEOUT"
        sock.settimeout(0)
        return ""

    sock.settimeout(0)

    if _debug: print >> sys.stderr, "Recv << : ", response

    # If the server doesn't return OK then we assume the process is not running.
    if len(response) == 0 or response != "OK":
        return ""

    # This can only be "OK" for now
    return response


def _get_socket(host, port, client=True):

    # This should handle both IPv4 and IPv6 systems.

    s = None
    for res in socket.getaddrinfo(host, port,
                                   socket.AF_UNSPEC, socket.SOCK_STREAM):

        af, socktype, proto, dummy_canonname, sa = res

        if _debug: print >> sys.stderr, "getaddrinfo: ", res

        try:
            s = socket.socket(af, socktype, proto)
        except socket.error:
            s = None
            continue
        try:
            # Client side socket
            if client:
                s.connect(sa)
            # Server side socket
            else:
                s.bind(sa)
                s.listen(5)
        except socket.error:
            s.close()
            s = None
            continue
        break

    return s


def _get_port_socket():

    host = "127.0.0.1"
    sock = None

    # Find an available port in the private range - 25 attempts
    for dummy in xrange(25):
        port = random.randrange(49152, 65535)
        if _debug: print >> sys.stderr, "Find Port: ", host, port
        sock = _get_socket(host, port, client=False)
        if sock is not None: break

    # We didn't find any available ports
    if sock is None: port = 0

    if _debug: print >> sys.stderr, "Using Port: ", host, port

    return port, sock


def _convert_lock(lock_type):

    if lock_type == 'nt_lock':
        return 'nt-1_lock'

    if lock_type == 'nt-0_lock':
        return 'nt_lock'

    if lock_type == 'ut_lock':
        return 'ut-1_lock'

    return lock_type
