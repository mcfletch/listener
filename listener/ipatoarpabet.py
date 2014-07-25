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
            MAPPING.setdefault(line[1].decode('utf-8'),[]).append( line[0].decode('utf-8'))
    return MAPPING

def get_espeak( word ):
    return subprocess.check_output([
        'espeak',
        '-q','--ipa=3',
        word,
    ]).decode('utf-8')
def translate( ipa ):
    result = []
    mapping = get_mapping()
    ipa = [
        c.strip() for c in 
        ipa.strip().replace(u' ',u'_').replace(
            u'ˌ',u''
        ).replace(
            u'ˈ',u''
        ).replace(
            u'ː', u''
        ).split(u'_')
    ]
    results = [ ]
    for sound in ipa:
        if sound in mapping:
            sound = [sound]
        for character in sound:
            if not character:
                continue
            translations = mapping.get(character)
            if not translations:
                raise ValueError( character, ipa )
            elif not results:
                results = translations[:]
            else:
                results = [ r+' '+t for r in results for t in translations]
    return results

def test():
    mapping = get_mapping()
    assert u'ɛ' in mapping, mapping.keys()
    dictionary = os.path.expanduser( '~/.config/listener/default/lm/dictionary.dict' )
    good = bad = 0
    try:
        for line in open(dictionary):
            try:
                word,description = line.strip().split('\t',1)
            except ValueError as err:
                err.args += (line,)
                raise
            if word.endswith( ')' ):
                word = word.rsplit('(',1)[0]
            while word and not word[0].isalnum():
                word = word[1:]
            ipa = get_espeak( word )
            try:
                translated = translate( ipa )
            except ValueError as err:
                err.args += (word,ipa)
                print( 
                    u'Failed to translate: %s %s -> %s  char=%s(%r)'%(
                    word,
                    ipa, description, err.args[0], err.args[0],
                ))
                raise
            if description in translated:
                good += 1
            else:
                bad += 1
                print( '%(word)s %(ipa)s\n\t%(translated)s\n\t%(description)s'%locals())
    finally:
        print '%s good %s bad %s'%(good,bad, (good/float(good+bad or 1)))

if __name__ == '__main__':
    test()
