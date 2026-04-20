"""
multiplayer, a Python library for managing multiplayer games
Copyright (C) 2025 [devfred78](https://github.com/devfred78)

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

This module provides tools to manage a log server
"""

import logging
from pathlib import Path
import pickle
import platform
import selectors
import socket
import sys
import threading
from time import sleep

from colorlog import ColoredFormatter
from colorlog.escape_codes import escape_codes

class OriginColoredFormatter(ColoredFormatter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.origin_colors = {
            "GameServer": "purple",
            "GameClient": "green",
            "GameAdmin": "red",
            "RemoteGame": "blue",
            "Observer": "cyan",
        }
        self.available_colors = ["blue", "cyan", "green", "purple", "red", "white", "yellow"]
        self._next_color_idx = 0
        self._assigned_colors = {}

    def format(self, record):
        # Use the name as origin
        origin = record.name
        # Try to find a specific color or assign one
        color = self.origin_colors.get(origin)
        if not color:
            # If the name is like "RemoteGame.Alice", try "RemoteGame"
            base_origin = origin.split('.')[0]
            color = self.origin_colors.get(base_origin)
            
        if not color:
            if origin not in self._assigned_colors:
                self._assigned_colors[origin] = self.available_colors[self._next_color_idx % len(self.available_colors)]
                self._next_color_idx += 1
            color = self._assigned_colors[origin]
        
        # Temporarily inject the color for the formatter
        # Use get to avoid KeyError if something goes wrong
        record.log_color = escape_codes.get(color, "")
        return super().format(record)

if __name__ != '__main__': 
    from . import UNIX_SOCKET_PATH
else:
    # local path
    if getattr(sys, "frozen", False):
        local_path = Path(sys.executable).parent
    else:
        local_path = Path(__file__).resolve().parent

    UNIX_SOCKET_PATH = local_path / Path('logging_socket')
    
class LoggingServer(threading.Thread):
    """
    This class implements a server that receives and processes logs transmitted by SocketHandler handlers. Like the client side, the server manages stream sockets (SOCK_STREAM sockets) from both the AF_UNIX and AF_INET families.
    
    The family is defined when the server is instantiated: if the port argument is None (its default value), then the family is AF_UNIX, and the host argument is used to define the file to be used (in this case, host can be either a pathlib.Path object or a string). Otherwise, the family is AF_INET.
    
    Warning: in the case of an AF_UNIX family, if *host* is filled in with an existing file, then it is deleted (provided you have the right to do so). It is therefore particularly advisable to provide a non-existent file, or to leave the default value.
    
    This class inherits from threading.Thread, meaning that it starts with the `start()` method, and it is NON blocking.
    """
    
    def __init__(self, host: Path = UNIX_SOCKET_PATH, port: int|None = None, timeout: int = 5, color_mode: str = "level"):
        
        super().__init__()
        
        # logging initialization
        self.logger = logging.getLogger("ServerLog")
        self.logger.setLevel(logging.NOTSET)
        handler = logging.StreamHandler()
        
        if color_mode == "origin":
            formatter = OriginColoredFormatter(
                "%(log_color)s[%(asctime)s][%(levelname)s][%(name)s]:%(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
                reset=True,
                style="%",
            )
        else:
            formatter = ColoredFormatter(
                "%(log_color)s[%(asctime)s][%(levelname)s][%(module)s]:%(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
                reset=True,
                log_colors={
                    "DEBUG": "cyan",
                    "INFO": "green",
                    "WARNING": "yellow",
                    "ERROR": "red",
                    "CRITICAL": "red,bg_white",
                },
                secondary_log_colors={},
                style="%",
            )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)


        if port is None and platform.system().lower() != "windows" : # AF_UNIX family
            self.address = str(host)
            host.unlink(missing_ok = True)  # Delete the socket file if existing
            sock_family = socket.AF_UNIX
        else: # AF_INET family
            self.address = (str(host), port)
            sock_family = socket.AF_INET
        
        # maximum wait time (in seconds) before detecting a closed connection
        self._timeout = timeout
        
        # Server socket creation
        self._socket = socket.socket(sock_family, socket.SOCK_STREAM)
        self._socket.settimeout(self._timeout)
    
    def run(self):
        """
        Waiting for connections until an error occurs or the `stop()` method is called.
        
        Automatically called by the `start()` method in a separated thread.
        """
        try:
            # Link the socket to the address
            self._socket.bind(self.address)
        except OSError:
            print(f"\x1b[31m!!! Another server is already running on the port {self.address[1]} !!!")
        else:
        
            # Enable the server to accept connections
            self._socket.listen()
            
            # Flags
            self._running = True # If True, the server is running
            
            # Internal variables
            self._sel = selectors.DefaultSelector() # Selector to deal with connections to clients
            self._registered_connections = list() # list of registered connections
            
            # Launch the logging loop (in a separated thread)
            threading.Thread(target = self._logging).start()
            
            while self._running:
                try:
                    conn, addr = self._socket.accept()
                    # print("CONNECTION ESTABLISHED !!")
                    conn.setblocking(False) # the connection is now non-blocking
                    # self._connections.append(conn)
                    self._sel.register(conn, selectors.EVENT_READ)
                    self._registered_connections.append(conn)
                    # print(f"Number of available connection(s): {len(self._registered_connections)}")
                except socket.timeout:
                    pass
                except socket.error as err:
                    print("\x1b[31m!!! SOCKET ERROR !!!")
                    print(err)
                    self.stop()
                    # break
    
    def stop(self):
        """
        Stop the server.
        """
        self._running = False
        try:
            self._socket.shutdown(socket.SHUT_RD)
        except OSError:
            # The connection has already been shutting down !
            pass
        else:
            self._socket.close()
    
    def _receive(self, sock: socket.socket, nb_bytes: int = 1) -> bytearray:
        """
        Receive `nb_bytes` bytes from the socket `sock`.
        
        Returns a bytearray of length `nb_bytes` containing the reveived bytes
        """
        
        received_bytes = list()
        for _ in range(nb_bytes):
            try:
                rbyte = sock.recv(1)
            except (ConnectionResetError, BrokenPipeError, OSError):
                rbyte = b''
            
            if rbyte == b'': # socket connection broken
                self._sel.unregister(sock)
                try:
                    sock.shutdown(socket.SHUT_RD)
                except OSError:
                    pass
                sock.close()
                if sock in self._registered_connections:
                    self._registered_connections.remove(sock)
                # print("CONNECTION CLOSED")
                # print(f"Number of remaining available connection(s): {len(self._registered_connections)}")
                if len(self._registered_connections) == 0:
                    print("No connection left: stopping the log server...")
                    self._running = False
                    self.stop()
                break
            else:
                # print(f"Received byte: {rbyte}")
                received_bytes.append(rbyte)
        return bytearray(b''.join(received_bytes))
    
    def _logging(self):
        """
        Print all strings given by connected clients.
        """
        sleep(2)
        print("Log server is now ready")
        while self._running:
            if len(self._registered_connections) > 0:
                events = self._sel.select(self._timeout)
                avail_conns = [key.fileobj for (key, mask) in events]
                
                # Check for connections to close
                for conn in list(self._registered_connections):
                    if conn not in avail_conns:
                        try:
                            self._sel.unregister(conn)
                        except KeyError:
                            pass
                        try:
                            conn.shutdown(socket.SHUT_RD)
                        except OSError:
                            pass
                        conn.close()
                        self._registered_connections.remove(conn)
                
                # Read receipt strings from available connections and print them on the standard output
                for conn in avail_conns:
                    # 4 first bytes indicate the message length in big-endian order
                    # See source code of makePickle() method from SocketHandler class in module [logging.handlers](https://github.com/python/cpython/blob/3.14/Lib/logging/handlers.py)
                    msg_length = int.from_bytes(self._receive(conn, 4), byteorder = 'big')
                    msg = self._receive(conn, msg_length)
                    try:
                        msg_dict = pickle.loads(msg)
                        record = logging.makeLogRecord(msg_dict)
                        self.logger.handle(record)
                    except UnicodeError:
                        print("\x1b[31m!!! LOG MESSAGE NOT ENCODED PROPERLY !!!")
                    except pickle.UnpicklingError:
                        print("\x1b[31m!!! UNABLE TO DECODE THE RECEIVED LOG MESSAGE !!!")
                    except EOFError:
                        # print("CONNECTION CLOSED")
                        # print(f"Number of remaining available connection(s): {len(self._registered_connections)}")
                        if len(self._registered_connections) == 0:
                            # print("No connection left: stopping the log server...")
                            self._running = False
                            self.stop()
                

def server(port:int = 5000, color_mode: str = "level"):
    print("****************************")
    print("*   Logging server         *")
    print(f"*    port = {port}           *")
    print(f"*    color mode = {color_mode}    *")
    print("****************************")
    print()
    lserv = LoggingServer(host = "localhost", port=port, color_mode=color_mode)
    lserv.start()
    try:
        lserv.join()
    except KeyboardInterrupt:
        lserv.stop()

if __name__ == '__main__':    
    ### Launch the logging server in a separated thread ###
    
    if len(sys.argv) >= 2:
        port = 5000
        color_mode = "level"
        
        if "--port" in sys.argv:
            idx = sys.argv.index("--port")
            try:
                port = int(sys.argv[idx + 1])
            except (ValueError, IndexError):
                pass
        
        if "--color-mode" in sys.argv:
            idx = sys.argv.index("--color-mode")
            try:
                color_mode = sys.argv[idx + 1]
            except IndexError:
                pass
                
        server(port, color_mode)
    else:
        server()
