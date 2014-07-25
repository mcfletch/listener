"""IPA to ARPABet pipeline/converter"""
# -*- coding: utf-8 -*-
import json
import pprint 
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

def kill_speaking_cues( word ):
    return word.strip().replace(
        u' ',u'_'
    ).replace(
        u'ˌ',u''
    ).replace(
        u'ˈ',u''
    ).replace(
        u'ː', u''
    ).replace(
        u'\u0303',''
    ).replace( u'__', u'_' )

def dictionary_espeak( ):
    dictionary = os.path.expanduser( '~/.config/listener/default/lm/dictionary.dict' )
    output_mapping = os.path.expanduser( '~/.config/listener/default/lm/dictionary.ipa' )
    mapping = {}
    mapped = 0
    i = 0
    with open( output_mapping, 'w') as output:
        for i,line in enumerate(open(dictionary)):
            word,description = line.strip().split('\t',1)
            ipa = get_espeak( clean_dict_word( word ) )
            ipa = ipa.encode('utf-8')
            output.write( '%s\t%s\t%s\n'%(word,description,ipa))
        if i %1000 == 0:
            print( i )
            

def get_espeak( word ):
    return kill_speaking_cues(subprocess.check_output([
        'espeak',
        '-q','--ipa=3',
        '-v', 'en-ca',
        word,
    ]).decode('utf-8'))
def _translate( ipa ):
    result = []
    mapping = get_mapping()
    ipa = [
        c.strip() for c in 
        ipa.split(u'_')
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

ALWAYS_MAPS = {
    't': 'T',
    'p': 'P',
    'n': 'N',
    'l': 'L',
}
def check_consonants( ipa, description ):
    """Check for mis-match on known-mapping consonants
    
    The idea here is to reduce the number of cases where 
    the ipa and arpa just *happen* to have the same number 
    of phonemes but they don't actually map...
    """
    for (i,d) in zip( ipa,description):
        if i in ALWAYS_MAPS:
            if d != ALWAYS_MAPS[i]:
                return False 
    return True

def stat_mapping( ):
    """Process the whole dictionary attempting to find IPA -> Arpabet mapping
    
    There are a *large* number of cases where the ipa and arpabet mappings 
    are not 1:1 and/or do not map known-mapping values
    """
    dictionary = os.path.expanduser( '~/.config/listener/default/lm/dictionary.dict' )
    mapping = {}
    mapped = 0
    i = 0
    try:
        for i,line in enumerate(open(dictionary)):
            word,description = line.strip().split('\t',1)
            word = clean_dict_word( word )
            description = description.split(' ')
            ipa_fragments = get_espeak( word ).split('_')
            if not len(ipa_fragments) == len(description):
                continue 
            if not check_consonants( ipa_fragments, description ):
                continue 
            for formal,arpa in zip( ipa_fragments, description ):
                possible = mapping.setdefault(formal,{})
                possible[arpa] = possible.get(arpa,0) + 1
            mapped += 1
            if i % 1000 == 0:
                print( '%s lines %s mapped'%(i+1,mapped))
    finally:
        table = json.dumps( {
            u'lines': i,
            u'mapping': mapping
        }, indent=2, ensure_ascii=False ).encode('utf-8')
        open( os.path.join( HERE,'ipastatmap.json'), 'w').write( table )
        print( table )

def clean_dict_word( word ):
    if word.endswith( ')' ):
        word = word.rsplit('(',1)[0]
    while word and not word[0].isalnum():
        word = word[1:]
    return word

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
            word = clean_dict_word( word )
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
    dictionary_espeak()
    #stat_mapping()
    #test()
