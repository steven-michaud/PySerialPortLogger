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
from threading import Thread, Event

# Secondary thread just for printing
def print_strings(strings_array):
    while True:
        print_ready.wait()
        print_ready.clear()
        if (not keep_going.is_set()):
            break

        while True:
            try:
                string = strings_array.pop(0)
                # Our input should already have newline characters in it. So
                # we set end to '' here, since we don't want print to add more
                # newlines.
                print(string, end='', file=sys.stderr)
            except IndexError:
                break

# Secondary thread just for reading from our TTY
def read_blobs(file, strings_array):
    with ExitStack() as stack:
        stack.enter_context(file)

        while True:
            read_ready.wait()
            read_ready.clear()
            if (not keep_going.is_set()):
                break

            binary_blobs = []
            while True:
                blob = file.readall()
                if (blob != None and len(blob) != 0):
                    binary_blobs.append(blob)
                if (blob == None or len(blob) == 0):
                    if (len(binary_blobs) != 0):
                        for item in binary_blobs:
                            # If our input is in UTF8 format, dividing it
                            # into blobs of arbitrary length may introduce
                            # formatting errors. We must ignore these errors
                            # when we convert the blobs into strings.
                            string = item.decode(errors='ignore')
                            strings_array.append(string)
                        print_ready.set()
                    # read_ready may have been set again (in run()) while we
                    # were reading previous input, so we take another round.
                    if (read_ready.is_set()):
                        read_ready.clear()
                        binary_blobs = []
                        continue
                    break

def run():
    """Creates a virtual serial port to which logging output can be directed
    from any process running in the same environment."""

    master_fd, slave_fd = pty.openpty()
    tty.setraw(master_fd)
    os.set_blocking(master_fd, False)
    slave_name = os.ttyname(slave_fd)
    # Open in binary mode without buffering, which is easier to deal with and
    # seems more efficient. Each binary blob will be converted to a string
    # before printing. Each line of input must end in a newline character
    # ('\n').
    master_file = open(master_fd, mode='rb', buffering=0)
    print('Ctrl-C to exit')
    print(slave_name)

    strings_array = []

    global keep_going
    keep_going = Event()
    keep_going.set()
    global print_ready
    print_ready = Event()
    print_ready.clear()
    global read_ready
    read_ready = Event()
    read_ready.clear()

    global print_thread
    print_thread = Thread(target=print_strings, args=[strings_array])
    print_thread.start()
    global read_thread
    read_thread = Thread(target=read_blobs, args=[master_file, strings_array])
    read_thread.start()

    with Selector() as selector:
        selector.register(master_fd, EVENT_READ)

        while True:
            for key, events in selector.select():
                if not events & EVENT_READ:
                    continue

            read_ready.set()

def main():
    parser = argparse.ArgumentParser (
        description='Create a virtual serial port, print its name to stdout '
                    'and wait for input. Open this serial port in your code '
                    'as a file, then write to it what you wish to log. Each '
                    'line must end in a newline character. Ctrl-C to exit.'
    )
    parser.add_argument('-v', '--version', action='store_true',
                        help='print version and exit')
    args = parser.parse_args()

    if (args.version):
        print('PySerialPortLogger version 2.0.0')
        sys.exit()

    # Catch KeyboardInterrupt so Ctrl-C doesn't print traceback.
    try:
        run()
    except KeyboardInterrupt:
        keep_going.clear()
        print_ready.set()
        read_ready.set()
        print_thread.join()
        read_thread.join()

if __name__ == '__main__':
    main()
