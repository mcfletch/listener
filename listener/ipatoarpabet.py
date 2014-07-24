"""IPA to ARPABet pipeline/converter"""
# -*- coding: utf-8 -*-

import os, csv, subprocess, codecs
HERE = os.path.dirname( __file__ )
MAPPING_FILE = os.path.join( HERE, 'ipatoarpabet.csv' )

MAPPING = None 
def get_mapping( ):
    global MAPPING
    if MAPPING is None:
        MAPPING = {}
        for line in csv.reader( open( MAPPING_FILE, 'rb' ) ):
            print line
            MAPPING.setdefault(line[1],[]).append( line[0])
    return MAPPING

def get_espeak( word ):
    return subprocess.check_output([
        'espeak',
        '--punct','-q','-x','--ipa=3',
        word,
    ])
def translate( ipa ):
    result = []
    mapping = get_mapping()
    ipa = ipa.strip().replace('ˌ','').replace('ˈ','').split('_')
    return ' '.join( [mapping.get(c,[c])[0] for c in ipa])

def test():
    dictionary = os.path.expanduser( '~/.config/listener/default/lm/dictionary.dict' )
    for line in open(dictionary):
        try:
            word,description = line.strip().split('\t',1)
        except ValueError as err:
            raise ValueError( line )
        if word.endswith( ')' ):
            word = word.rsplit('(',1)[0]
        ipa = get_espeak( word )
        try:
            translated = translate( ipa )
        except ValueError as err:
            print( 'Failure on %r %s %s'%( word, ipa, err.args[0] ))
            break
        print( '%(word)s %(ipa)s %(translated)s'%locals())

if __name__ == '__main__':
    test()
