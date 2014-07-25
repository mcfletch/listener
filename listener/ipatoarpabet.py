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
        '-v', 'en-ca',
        word,
    ]).decode('utf-8')
def _translate( ipa ):
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
        ).replace(
            u'\u0303',''
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
                print (u'Unrecognized ipa: %s'%(character))
                continue
                #raise ValueError( character, ipa )
            elif not results:
                results = translations[:]
            else:
                results = [ r+' '+t for r in results for t in translations if t]
    return results

def translate( word ):
    ipa = get_espeak( word )
    try:
        return _translate( ipa )
    except ValueError as err:
        err.args += (word,ipa)
        raise

def test():
    mapping = get_mapping()
    assert u'ɛ' in mapping, mapping.keys()
    dictionary = os.path.expanduser( '~/.config/listener/default/lm/dictionary.dict' )
    good = bad = 0
    try:
        for i,line in enumerate(open(dictionary)):
            try:
                word,description = line.strip().split('\t',1)
            except ValueError as err:
                err.args += (line,)
                raise
            if word.endswith( ')' ):
                word = word.rsplit('(',1)[0]
            while word and not word[0].isalnum():
                word = word[1:]
            try:
                translated = translate( word )
            except ValueError as err:
                print( 
                    u'Failed to translate: %s (%s) -> %s  char=%s(%r)'%(
                    word,
                    err.args[1],
                    description, 
                    err.args[0], err.args[0],
                ))
                raise
            if description in translated:
                good += 1
            else:
                bad += 1
                our_options = "\n\t\t".join( translated )
                ipa = get_espeak( word )
                print( '%(word)s %(ipa)s\n\t\n\t%(description)s\n\t\t%(our_options)s'%locals())
            if not i%1000:
                print '%s good %s bad %0.3f'%(good,bad, (good/float(good+bad or 1)))
    finally:
        print '%s good %s bad %s'%(good,bad, (good/float(good+bad or 1)))

if __name__ == '__main__':
    test()
