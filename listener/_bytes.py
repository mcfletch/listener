import sys

STR_IS_BYTES = True

if sys.version_info[:2] < (2,6):
    # no bytes, traditional setup...
    bytes = str 
else:
    bytes = bytes
try:
    long = long
except NameError as err:
    long = int
if sys.version_info[:2] < (3,0):
    # traditional setup, with bytes defined...
    unicode = unicode
    _NULL_8_BYTE = '\000'
    def as_bytes( x, encoding='utf-8' ):
        if isinstance( x, unicode ):
            return x.encode( encoding )
        return bytes( x )
    def as_unicode( x, encoding='utf-8'):
        if isinstance( x, bytes ):
            return x.decode(encoding)
        return unicode(x)
    integer_types = int,long
else:
    # new setup, str is now unicode...
    STR_IS_BYTES = False
    _NULL_8_BYTE = bytes( '\000','latin1' )
    def as_bytes( x, encoding='utf-8' ):
        if isinstance( x,unicode ):
            return x.encode(encoding)
        elif isinstance( x, bytes ):
            # Note: this can create an 8-bit string that is *not* in encoding,
            # but that is potentially exactly what we wanted, as these can 
            # be arbitrary byte-streams being passed to C functions
            return x
        return str(x).encode( encoding )
    def as_unicode( x, encoding='utf-8'):
        if isinstance( x, bytes ):
            return x.decode(encoding)
        return unicode(x)
    unicode = str
    integer_types = int,

STR_IS_UNICODE = not STR_IS_BYTES
if hasattr( sys, 'maxsize' ):
    maxsize = sys.maxsize 
else:
    maxsize = sys.maxint
