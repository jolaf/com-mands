#!/usr/bin/python

from binascii import hexlify
from glob import glob
from itertools import chain
from os import devnull
from shlex import split
from subprocess import call
from sys import argv, exit # pylint: disable=W0622

DEVICE_CLASSES = ('', '/dev/ttyS%p', '/dev/ttyUSB%p') # should cover most platforms
PORTS = chain.from_iterable((d.replace('%p', str(i)) if d else i for d in DEVICE_CLASSES) for i in xrange(256))

TAG = '%c'              # Tag in file mask to be replaced with card ID
COMMAND_PREFIX = 'ID: ' # ID prefix in serial port stream

DEVNULL = open(devnull, 'w')

def _error(message):
    print "ERROR: %s" % message

def error(message):
    _error(message)
    exit()

def usage(message = ''):
    if message:
        print
        _error(message)
    print "\nUsage: COMmands help - show this help\n" \
            "       COMmands [show] - just show input from a port\n" \
            "       COMmands start [mask] - open files/folders by commands prefixed by %s" % TAG
    exit()

try:
    from serial import Serial
except:
    error("Please install pySerial: http://pypi.python.org/pypi/pyserial")

def port(p = None): # generator
    serial = None
    if p != None:
        try:
            serial = Serial(p) # , BAUDRATE)
        except:
            pass
    else:
        for p in PORTS:
            try:
                serial = Serial(p) # , BAUDRATE)
                break
            except:
                pass
    if not serial:
        error("Could not find an available COM port")
    print "! %s" % ('COM%d' % (p + 1) if type(p) == int else p)
    for line in serial:
        yield line

def main():
    if len(argv) < 2 or argv[1].lower() == 'show':
        for line in (line.strip() for line in port()):
            print "> %s (%s)" % (hexlify(line), repr(line))
    elif argv[1].lower() in ('help', '-help', '--help', '-h', '/?'):
        usage()
    elif argv[1].lower() == 'start':
        if len(argv) < 3:
            command = (TAG,)
        else:
            command = split(' '.join(argv[2:]))
            if all(c.find(TAG) < 0 for c in command):
                usage("Usage: mask must contain %s" % TAG)
        for line in (line.strip() for line in port()):
            print "> %s (%s)" % (hexlify(line), repr(line))
            if line.startswith(COMMAND_PREFIX):
                words = []
                for word in command:
                    if TAG in word:
                        word = word.replace(TAG, line[len(COMMAND_PREFIX):].upper())
                        files = glob(word)
                        if files:
                            word = files[0]
                    words.append(word)
                print "$ %s" % ' '.join(words),
                ret = call(words, shell = True, stdin = DEVNULL, stdout = DEVNULL, stderr = DEVNULL)
                print ("(ERROR: %d)" % ret) if ret else "(OK)"
    else:
        usage("Unknown command: %s" % argv[1])

if __name__ == '__main__':
    main()
