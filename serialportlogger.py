# The MIT License (MIT)
#
# Copyright (c) 2022 Steven Michaud
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# Copyright 2021 Ezra Morris
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import argparse
from contextlib import ExitStack
import os
import pty
from selectors import DefaultSelector as Selector, EVENT_READ
import sys
import tty

def run():
    """Creates a virtual serial port to which logging output can be directed
    from any process running in the same environment."""

    master_fd, slave_fd = pty.openpty()
    tty.setraw(master_fd)
    os.set_blocking(master_fd, False)
    slave_name = os.ttyname(slave_fd)
    # Open in text mode, to receive text input. Each line of input must end
    # in a newline character ('\n').
    master_file = open(master_fd, mode='r+t', buffering=1)
    print('Ctrl-C to exit')
    print(slave_name)

    with Selector() as selector, ExitStack() as stack:
        stack.enter_context(master_file)
        selector.register(master_fd, EVENT_READ)

        while True:
            # Each EVENT_READ event marks the receipt of a newline character,
            # plus whatever other characters might have preceded it.
            for key, events in selector.select():
                if not events & EVENT_READ:
                    continue

                data = master_file.read()
                print(data, end='', file=sys.stderr)

def main():
    parser = argparse.ArgumentParser (
        description='Create a virtual serial port, print its name to stdout '
                    'and wait for input. Open this serial port in your code '
                    'as a file, then write to it what you wish to log. Each '
                    'line must end in a newline character. Ctrl-C to exit.'
    )
    args = parser.parse_args()

    # Catch KeyboardInterrupt so Ctrl-C doesn't print traceback.
    try:
        run()
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    main()
