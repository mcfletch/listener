"""Spike test for uinput generation of key events"""
import os, sys, logging, select, fcntl, time, json
import ctypes
import contextlib
log = logging.getLogger( __name__ )
HERE = os.path.dirname( __file__ )
KEY_MAPPING_FILE = os.path.join( HERE, 'uinput-mapping.json' )

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

class UInput( object ):
    def __init__( self ):
        self.open_fd()
        # Yes, this sucks, but it takes a while to be recognized
        time.sleep( .01 )

    @property
    def our_device( self ):
        return uinput_user_dev(
            name = 'listener voice keyboard',
            id = input_id(
                bustype=BUS_VIRTUAL,
                vendor=1,
                product=1,
                version=1,
            ),
        )
    
    @property
    def uinput_device(self):
        for fn in UINPUT_LOCATIONS:
            if os.path.exists( fn ):
                return fn 
        raise RuntimeError( "Did not find uinput device" )

    def write_bytes( self, bytes ):
        original = bytes
        while bytes:
            written = os.write(self.fd, bytes )
            if written == 0:
                raise RuntimeError( 'Unable to write to input device?' )
            else:
                bytes = bytes[written:]
        return original

    def open_fd( self, filename=None ):
        filename = filename or self.uinput_device
        self.fd = os.open( filename, os.O_WRONLY|os.O_NONBLOCK )
        for typ in (EV_KEY,EV_SYN):
            if fcntl.ioctl(self.fd, UI_SET_EVBIT, typ) < 0:
                raise RuntimeError( 'Unable to set event bit %s'%(typ,) )
        for i in range(256):
            if fcntl.ioctl(self.fd, UI_SET_KEYBIT, i) < 0:
                raise RuntimeError( 'Unable to set key code %s bit', i )
        device = self.our_device
        as_string = ctypes.string_at( ctypes.addressof(device),ctypes.sizeof(device) )
        self.write_bytes( as_string )
        if fcntl.ioctl( self.fd, UI_DEV_CREATE ) < 0:
            raise RuntimeError( 'Unable to create virtual device' )

    def _send_event( self, type=EV_KEY, code=65, value=1 ):
        event = input_event(
            type=type,
            code=code,
            value=value,
        )
        as_string = ctypes.string_at( ctypes.addressof(event),ctypes.sizeof(event))
        self.write_bytes( as_string )

    @contextlib.contextmanager
    def key_pressed( self, code ):
        if isinstance( code, (str,unicode)):
            code = self.get_key_mapping()[code]
        self._send_event( code=code, value=1 )
        yield 
        self._send_event( code=code, value=0 )
    
    def send_keypress( self, key='a'):
        mapping = self.get_key_mapping()
        uc = key.upper()
        if uc in mapping:
            code = mapping[uc]
        else:
            log.warn( 'Could not find mapping for key %r', key )
            return
        if not key.islower():
            # we want to be able to pass explicit command codes as uppercase too
            with self.key_pressed(code=mapping['RIGHTSHIFT']):
                with self.key_pressed(code=code):
                    log.debug( 'Sending key %r(%r)', key, code )
                    pass
        else:
            with self.key_pressed(code=code):
                log.debug( 'Sending key %r(%r)', key, code )
                pass
    
    def sync(self):
        self._send_event( type=EV_SYN, code=SYN_REPORT,value=0)
    
    KEY_MAPPING = None
    @classmethod
    def get_key_mapping(cls,force_rescan=False):
        if cls.KEY_MAPPING is None:
            if (not force_rescan) and os.path.exists( KEY_MAPPING_FILE ):
                cls.KEY_MAPPING = json.loads( open(KEY_MAPPING_FILE).read())
            else:
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
                cls.KEY_MAPPING = mapping
        return cls.KEY_MAPPING
    def close( self ):
        if fcntl.ioctl(self.fd, UI_DEV_DESTROY) < 0:
            raise RuntimeError( 'Unable to cleanly shut down device' )
        
    
def main():
    logging.basicConfig( level=logging.INFO )
    uinput = UInput()
    try:
        with uinput.key_pressed( 'LEFTALT' ):
            with uinput.key_pressed( 'TAB' ):
                log.info( 'Switching to another window' )
        uinput.sync()
        # sigh, again, takes a while to switch and the input system 
        # doesn't take into account that alt-tab was intended to switch 
        # focus to a new window :( 
        time.sleep( .1 )
        for char in 'hello world':
            uinput.send_keypress(char)
    finally:
        uinput.close()

def rebuild_mapping():
    mapping = UInput.get_key_mapping(force_rescan=True)
    content = json.dumps( mapping )
    with open( KEY_MAPPING_FILE,'w' ) as fh:
        fh.write( content )

if __name__ == "__main__":
    main()
