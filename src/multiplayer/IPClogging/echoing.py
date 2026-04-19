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

"""
Simple Python script echoing in the standard output what is given in the standard input.

Exits if the stdin is b"EXIT" (in capitals)
"""

from sys import exit

while(True):
    print("Waiting for stdin...")
    raw_data = input()
    # raw_data = stdin.read()
    print(f"Input receipt !: {raw_data}")
    if 'EXIT' in raw_data:
        exit(0)
    print(raw_data, flush = True)
    # stdout.write(raw_data)
    # stdout.flush()