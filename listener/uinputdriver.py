"""Spike test for uinput generation of key events"""
import os, sys, logging, select, fcntl
import ctypes
log = logging.getLogger( __name__ )

ABS_MAX = 0x3f
ABS_CNT = ABS_MAX + 1
BUS_VIRTUAL = 0x06
UI_DEV_CREATE = 0x5501
UI_DEV_DESTROY = 0x5502
UI_SET_EVBIT = 0x40045564
UI_SET_KEYBIT = 0x40045565
EV_KEY = 0x1

class input_id( ctypes.Structure ):
    _fields_ = [
        ('bustype',ctypes.c_uint16),
        ('vendor',ctypes.c_uint16),
        ('product',ctypes.c_uint16),
        ('version',ctypes.c_uint16),
    ]

class uinput_user_dev( ctypes.Structure ):
    _fields_ = [
        ('name',ctypes.c_char*80),
        ('id',input_id),
        ('ff_effects_max',ctypes.c_uint32),
        ('absmax',ctypes.c_int32*ABS_CNT),
        ('absmin',ctypes.c_int32*ABS_CNT),
        ('absfuzz',ctypes.c_int32*ABS_CNT),
        ('absflat',ctypes.c_int32*ABS_CNT),
    ]


UINPUT_LOCATIONS = [
    '/dev/uinput',
    '/dev/input/uinput',
]

def our_device( ):
    return uinput_user_dev(
        name = 'listener voice keyboard',
        id = input_id(
            bustype=BUS_VIRTUAL,
            vendor=1,
            product=1,
            version=1,
        ),
    )
    

def uinput_device():
    for fn in UINPUT_LOCATIONS:
        if os.path.exists( fn ):
            return fn 
    raise RuntimeError( "Did not find uinput device" )

def open_fd( filename=None ):
    filename = filename or uinput_device()
    fd = os.open( filename, os.O_WRONLY|os.O_NONBLOCK )
    if fcntl.ioctl(fd, UI_SET_EVBIT, EV_KEY) < 0:
        raise RuntimeError( 'Unable to set event bits' )
    for i in range(256):
        if fcntl.ioctl(fd, UI_SET_KEYBIT, i) < 0:
            raise RuntimeError( 'Unable to set key code %s bit', i )
    device = our_device()
    as_string = ctypes.string_at( ctypes.addressof(device),ctypes.sizeof(device) )
    written = os.write( 
        fd, 
        as_string
    )
    if fcntl.ioctl( fd, UI_DEV_CREATE ) < 0:
        raise RuntimeError( 'Unable to create virtual device' )
    return fd

def main():
    logging.basicConfig( level=logging.INFO )
    fd = open_fd( )
    try:
        pass 
    finally:
        if fcntl.ioctl(fd, UI_DEV_DESTROY) < 0:
            raise RuntimeError( 'Unable to cleanly shut down device' )

if __name__ == "__main__":
    main()
