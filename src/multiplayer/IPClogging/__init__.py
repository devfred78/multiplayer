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
"""

"""This package provides tools to manage a local IPC (Inter Process Communication) logging system"""

import os
from pathlib import Path
import subprocess
import sys

# local path
if getattr(sys, "frozen", False):
    local_path = Path(sys.executable).parent
else:
    local_path = Path(__file__).resolve().parent

UNIX_SOCKET_PATH = local_path / Path('logging_socket')

# echoing_path = local_path / Path('echoing.py')

# with subprocess.Popen(['wt', 'new-tab', 'cmd', '/k', 'uv', 'run', 'python', str(echoing_path)], stdin = subprocess.PIPE, shell = True) as terminal:
# # with subprocess.Popen(['uv', 'run', 'python', str(echoing_path)], stdin = subprocess.PIPE, shell = True) as terminal:
    # terminal.stdin.write(b'Hello/n')
    # terminal.stdin.flush()
    # terminal.stdin.write(b'Word !/n')
    # terminal.stdin.flush()
    # terminal.stdin.write(b'EXIT')
    # terminal.stdin.flush()

