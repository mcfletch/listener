#! /usr/bin/env python
from __future__ import absolute_import
from __future__ import print_function
import unicodedata


def main():
    fragments = set()
    def has_digit( x ):
        if x in fragments:
            return False
        for c in x:
            if c.isdigit():
                return True 
        return False
    for charrange in [
        xrange( 0, 0xFF ),
        xrange( 0x100, 0xFFFF ),
        xrange( 0x10000, 0x1FFFF ),
        xrange( 0x20000, 0x2FFFF ),
        xrange( 0xE0000, 0xEFFFF )
    ]:
        for i in charrange:
            char = unichr( i )
            try:
                name = unicodedata.name( char )
            except ValueError as err:
                continue
            description = [x for x in name.replace('-',' ').split() if not has_digit( x )]
            for fragment in description:
                fragments.add( fragment )
            print(u'%s\t%s\t%s'%( i, char, name ))
    print(sorted( fragments ))
    print(len(fragments))

if __name__ == "__main__":
    main()
    
