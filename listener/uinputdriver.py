"""Spike test for uinput generation of key events"""
import os, sys, logging, select, fcntl, time
import ctypes
log = logging.getLogger( __name__ )

ABS_MAX = 0x3f
ABS_CNT = ABS_MAX + 1
BUS_VIRTUAL = 0x06
UI_DEV_CREATE = 0x5501
UI_DEV_DESTROY = 0x5502
UI_SET_EVBIT = 0x40045564
UI_SET_KEYBIT = 0x40045565
EV_SYN = 0x00
EV_KEY = 0x1
SYN_REPORT = 0

class input_id( ctypes.Structure ):
    _fields_ = [
        ('bustype',ctypes.c_uint16),
        ('vendor',ctypes.c_uint16),
        ('product',ctypes.c_uint16),
        ('version',ctypes.c_uint16),
    ]
class timeval( ctypes.Structure ):
    _fields_ = [
        ('tv_sec',ctypes.c_ssize_t),
        ('tv_usec',ctypes.c_ssize_t),
    ]
class input_event( ctypes.Structure ):
    _fields_ = [
        ('time',timeval),
        ('type',ctypes.c_uint16),
        ('code',ctypes.c_uint16),
        ('value',ctypes.c_int32),
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

def write_bytes( fd, bytes ):
    original = bytes
    while bytes:
        written = os.write(fd, bytes )
        if written == 0:
            raise RuntimeError( 'Unable to write to input device?' )
        else:
            bytes = bytes[written:]
    return original

def open_fd( filename=None ):
    filename = filename or uinput_device()
    fd = os.open( filename, os.O_WRONLY|os.O_NONBLOCK )
    for typ in (EV_KEY,EV_SYN):
        if fcntl.ioctl(fd, UI_SET_EVBIT, typ) < 0:
            raise RuntimeError( 'Unable to set event bit %s'%(typ,) )
    for i in range(256):
        if fcntl.ioctl(fd, UI_SET_KEYBIT, i) < 0:
            raise RuntimeError( 'Unable to set key code %s bit', i )
    device = our_device()
    as_string = ctypes.string_at( ctypes.addressof(device),ctypes.sizeof(device) )
    write_bytes( fd, as_string )
    if fcntl.ioctl( fd, UI_DEV_CREATE ) < 0:
        raise RuntimeError( 'Unable to create virtual device' )
    return fd

def _send_event( fd, type=EV_KEY, code=65, value=1 ):
    event = input_event(
        type=type,
        code=code,
        value=value,
    )
    as_string = ctypes.string_at( ctypes.addressof(event),ctypes.sizeof(event))
    write_bytes( fd, as_string )

def send_keypress( fd, key='a'):
    mapping = get_key_mapping()
    uc = key.upper()
    if uc in mapping:
        code = mapping[uc]
    else:
        log.warn( 'Could not find mapping for key %r', key )
        return
    if not key.islower():
        # we want to be able to pass explicit command codes as uppercase too
        log.debug( 'Setting shift' )
        _send_event( fd, code=mapping['RIGHTSHIFT'], value=1 )
    log.debug( 'Sending key %r(%r)', key, code )
    _send_event( fd, code=code, value=1 )
    _send_event( fd, code=code, value=0 )
    if not key.islower():
        # we want to be able to pass explicit command codes as uppercase too
        _send_event( fd, code=mapping['RIGHTSHIFT'], value=0 )

def sync(fd):
    _send_event( fd, type=EV_SYN, code=SYN_REPORT,value=0)
    _send_event( fd, type=EV_SYN, code=SYN_REPORT,value=1)
        
def main():
    logging.basicConfig( level=logging.INFO )
    fd = open_fd( )
    # Sigh, there's a setup/negotiation time before the driver is 
    # able to send events... but there doesn't seem to be a way to 
    # get a notification when it is over...
    time.sleep( .01 )
    try:
        for char in 'hello world':
            send_keypress(fd,char)
    finally:
        if fcntl.ioctl(fd, UI_DEV_DESTROY) < 0:
            raise RuntimeError( 'Unable to cleanly shut down device' )

KEY_MAPPING = None
def get_key_mapping():
    global KEY_MAPPING
    if KEY_MAPPING is None:
        lines = open( '/usr/include/linux/input.h' ).readlines()
        mapping = {}
        for key,value in [
            line[8:].strip().split()[:2] 
            for line in lines if line.startswith( '#define KEY_' )
        ]:
            try:
                value = int(value)
            except ValueError as err:
                pass 
            else:
                mapping[key[4:]] = value 
        mapping[' '] = mapping['SPACE']
        KEY_MAPPING = mapping
    return KEY_MAPPING

if __name__ == "__main__":
    main()
