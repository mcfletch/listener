#! /usr/bin/env python
"""text2wfreq implementation in Python

This doesn't try to be efficient, as the word-sets we are looking at 
are really quite tiny...
"""
import re, sys

def main():
    counts = {}
    for line in sys.stdin.read().splitlines():
        words = line.split()
        for word in words:
            counts[word] = counts.get(word,0)+1
    counts = counts.items()
    counts.sort( key=lambda x: x[1],reverse=True )
    for key,value in counts:
        sys.stderr.write( '%s %d\n'%(key,value))

if __name__ == "__main__":
    main()
