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

Script that sends logs to the logging server
"""

import logging
from logging.handlers import SocketHandler
from pathlib import Path
import subprocess
import sys
from time import sleep

# local path
if getattr(sys, "frozen", False):
    local_path = Path(sys.executable).parent
else:
    local_path = Path(__file__).resolve().parent

UNIX_SOCKET_PATH = local_path / Path('logging_socket')

logger = logging.getLogger(__name__)

def main(port:int = 5000):
    logger.setLevel(logging.INFO)
    handler = SocketHandler("localhost", port)
    logger.addHandler(handler)
    
    server_path = local_path / Path('server.py')
    subprocess.run(['wt', 'new-tab', 'cmd', '/k', 'uv', 'run', 'python', str(server_path), '--port', str(port)], stdin = subprocess.PIPE, shell = True)
    
    print("Waiting for 2 secs before sending logs...")
    sleep(2)
    print("Debug logging")
    logger.debug("This is a DEBUG message")
    print("Info logging")
    logger.info("This is an INFO message")
    print("Warning logging")
    logger.warning("This is a WARNING message")
    print("Error logging")
    logger.error("This is an ERROR message")
    print("Critical logging")
    logger.critical("This is a CRITICAL message")
    print("Error logging")
    logger.error("This is an ERROR message")
    print("Warning logging")
    logger.warning("This is a WARNING message")
    print("Info logging")
    logger.info("This is an INFO message")
    print("Debug logging")
    logger.debug("This is a DEBUG message")
    
    input("Please push ENTER to finish...")

if __name__ == '__main__':
    port = 5005
    main(port)