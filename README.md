# PySerialPortLogger

PySerialPortLogger is a utility that makes it easy to log text output
in a complex environment on a POSIX system. Let's say you're trying to
debug an open-source application with many components and tens of
thousands of lines of code: You might try inserting logging commands
at strategic points in the code. Or you've injected a module into a
closed-source application, and need to log the information it finds
there. Then you discover your output is redirected light years away,
or to `/dev/null`. If you're doing this in a POSIX environment,
PySerialPortLogger is for you.

Use the following command to install PySerialPortLogger:

```
pip3 install PySerialPortLogger
```

Then run `serialportlogger` in a terminal window, and you'll see
output like the following:

```
% serialportlogger
Ctrl-C to exit
/dev/ttys002
```

All text output written to `/dev/ttys002` will get written to your
terminal window. Each line of output needs to end with a newline
character (`\n`).

Here are code fragments, in C and Python, which you can use to write
to this serial port:

```
#include <stdio.h>
#include <fcntl.h>

int virtual_serial_port_fd = -1;
FILE *virtual_serial_port_FILE = NULL;

virtual_serial_port_fd =
  open("/dev/ttys002", O_WRONLY | O_NONBLOCK | O_NOCTTY);
if (virtual_serial_port_fd >= 0) {
  virtual_serial_port_FILE = fdopen(virtual_serial_port_fd, "w");
}

while([have lines of text to log]) {
  if (virtual_serial_port_FILE) {
    fputs([newline-terminated line of text], virtual_serial_port_FILE);
  }
}

if (virtual_serial_port_FILE) {
  fclose(virtual_serial_port_FILE);
}
if (virtual_serial_port_fd) {
  close(virtual_serial_port_fd);
}
```

```
from contextlib import ExitStack

serial_port = open('/dev/ttys002', mode='wt', buffering=1)
ExitStack().enter_context(serial_port)
while [have lines of text to log]:
    serial_port.write([newline-terminated line of text])

```

PySerialPortLogger is based on another Github project named
[PyVirtualSerialPorts](https://github.com/ezramorris/PyVirtualSerialPorts)
