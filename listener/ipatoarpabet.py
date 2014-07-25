"""IPA to ARPABet pipeline/converter"""
# -*- coding: utf-8 -*-
import json
import pprint 
import os, csv, subprocess, codecs
import logging
log = logging.getLogger( __name__ )

HERE = os.path.dirname( __file__ )
MAPPING_FILE = os.path.join( HERE, 'ipatoarpabet.csv' )
STAT_MAP_FILE = os.path.join( HERE,'ipastatmap.json')

MAPPING = None 
def get_mapping( ):
    global MAPPING
    if MAPPING is None:
        MAPPING = {}
        for line in csv.reader( open( MAPPING_FILE, 'rb' ) ):
            MAPPING.setdefault(line[1].decode('utf-8'),[]).append( line[0].decode('utf-8'))
    return MAPPING

STAT_MAPPING = None 
def get_stat_mapping( ):
    global STAT_MAPPING
    if STAT_MAPPING is None:
        STAT_MAPPING = json.loads( open( STAT_MAP_FILE ).read())['mapping']
    return STAT_MAPPING

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
    ).replace(
        u'ʲ', '',
    ).replace( u'__', u'_' )

def dictionary_espeak( ):
    """Annotate the default dictionary with espeak results 
    
    This is done to facilitate playing with use of espeak pronunciations
    across the entire dictionary (in order to produce statistical mappings).
    
    Otherwise it takes a *very* long time to iterate with the various 
    strategies (since running espeak takes quite a while per word).
    
    Assumes that you've already got your 'default' context's dictionary.dict 
    created, produces a dictionary.ipa next to it...
    """
    output_mapping = os.path.expanduser( '~/.config/listener/default/lm/dictionary.ipa' )
    if not os.path.exists( output_mapping ):
        log.warn( 'Running IPA conversion, this will take 1/2 hour or more' )
        dictionary = os.path.expanduser( '~/.config/listener/default/lm/dictionary.dict' )
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
                log.info( 'Converting word %s', i )
    return output_mapping

def get_espeak( word, voice='en-ca' ):
    """Get espeak ipa (in ipa=3 format) for the given word in en-ca voice"""
    return kill_speaking_cues(subprocess.check_output([
        'espeak',
        '-q','--ipa=3',
        '-v', voice,
        word,
    ]).decode('utf-8'))
def _stat_translate( ipa ):
    result = []
    mapping = get_stat_mapping()
    ipa = _expand_rs( [
        c.strip() for c in 
        ipa.split(u'_')
    ] )
    results = []
    for sound in ipa:
        if not sound:
            continue 
        if not sound in mapping:
            log.error(u'Unrecognized ipa: %s', sound)
        translations = mapping.get(sound)
        if not translations:
            log.error(u'Unrecognized ipa: %s', sound)
            continue
        # choose the most likely 
        translations = [ t[0] for t in translations if t[1] > .2 ]
        if not results:
            results = translations[:]
        else:
            results = [ r+' '+t for r in results for t in translations if t]
    return results
    
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
                log.error(u'Unrecognized ipa: %s', character)
                continue
                #raise ValueError( character, ipa )
            elif not results:
                results = translations[:]
            else:
                results = [ r+' '+t for r in results for t in translations if t]
    return results

def translate( word, ipa=None ):
    if ipa is None:
        ipa = get_espeak( word )
    try:
        return _stat_translate( ipa )
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

def frequency_table( count_table, threshold=0.05 ):
    result = {}
    for (ipa,counts) in count_table.items():
        counts = sorted( counts.items(), key=lambda x: x[1], reverse=True )
        total = float(sum([c[1] for c in counts]))
        counts = [
            x for x in 
            [
                (p,count/total) 
                for (p,count) in counts
            ] 
            if x[1] >= threshold
        ]
        result[ipa] = counts 
    return result
def _expand_rs( ipa ):
    """Expands ipa r-suffixes, as they generally translate to two sounds in arpa"""
    for i in range(len(ipa)-1, -1, -1):
        if len(ipa[i]) < 2:
            continue
        if ipa[i].endswith(u'r'):
            ipa[i:i+1] = [ipa[i][:-1],u'r']
    return ipa
    
def create_stat_mapping( ):
    """Process the whole dictionary attempting to find IPA -> Arpabet mapping
    
    There are a *large* number of cases where the ipa and arpabet mappings 
    are not 1:1 and/or do not map known-mapping values
    """
    dictionary = dictionary_espeak()
    mapping = {}
    mapped = 0
    i = 0
    try:
        # first pass, look for extremely likely mappings...
        # these will be things that are 1:1 mappings with maybe some 
        # noise from mis-matches...
        for i,line in enumerate(open(dictionary)):
            word,description,ipa = line.strip().split('\t')
            word = word.decode('utf-8')
            description = description.decode('utf-8')
            ipa = ipa.decode('utf-8')
            description = description.split(' ')
            ipa_fragments = _expand_rs( ipa.split('_'))
            if not len(ipa_fragments) == len(description):
                continue 
#            if not check_consonants( ipa_fragments, description ):
#                continue 
            for formal,arpa in zip( ipa_fragments, description ):
                possible = mapping.setdefault(formal,{})
                possible[arpa] = possible.get(arpa,0) + 1
            mapped += 1
            if i % 1000 == 0:
                log.info( '%s lines %s mapped',i+1,mapped)
        
    finally:
        table = json.dumps( {
            u'lines': i,
            u'mapping': frequency_table(mapping),
        }, indent=2, ensure_ascii=False ).encode('utf-8')
        log.info( 'Writing statistics to: %s', STAT_MAP_FILE )
        open( STAT_MAP_FILE, 'w').write( table )

def clean_dict_word( word ):
    if word.endswith( ')' ):
        word = word.rsplit('(',1)[0]
    while word and not word[0].isalnum():
        word = word[1:]
    return word

def test():
    dictionary = dictionary_espeak()
    good = bad = total_tlength = 0
    try:
        for i,line in enumerate(open(dictionary)):
            try:
                word,description,ipa = [
                    x.decode('utf-8') for x in line.strip().split('\t')
                ]
            except ValueError as err:
                err.args += (line,)
                raise
            word = clean_dict_word( word )
            try:
                translated = translate( word, ipa )
            except ValueError as err:
                print( 
                    u'Failed to translate: %s (%s) -> %s  char=%s(%r)'%(
                    word,
                    err.args[1],
                    description, 
                    err.args[0], err.args[0],
                ))
                raise
            total_tlength += len(translated)
            if description in translated:
                good += 1
            else:
                bad += 1
                our_options = "\n\t\t".join( translated )
#                ipa = get_espeak( word )
#                print( '%(word)s %(ipa)s\n\t\n\t%(description)s\n\t\t%(our_options)s'%locals())
            if not i%1000:
                print '%s good %s bad %0.3f avg choices %s'%(good,bad, (good/float(good+bad or 1)), total_tlength/(good+bad))
    finally:
        print '%s good %s bad %s'%(good,bad, (good/float(good+bad or 1)))

if __name__ == '__main__':
    logging.basicConfig( level=logging.INFO )
    #dictionary_espeak()
    #stat_mapping()
    test()
