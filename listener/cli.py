"""Base argument parser for listener utilities"""
import argparse, logging, functools, os, sys, traceback

def base_arguments(purpose):
    parser = argparse.ArgumentParser(description=purpose)
    parser.add_argument(
        '--context',type=str,nargs=1,
        help='Voice dictation context to use (default is "default")',
        default='default',
    )
    return parser

def with_logging( function ):
    @functools.wraps( function )
    def logging_wrapper( *args, **named ):
        logging.basicConfig( level=logging.INFO )
        try:
            return function( *args, **named )
        except Exception as err:
            logging.getLogger('__main__').error( 
                'Crashed during main function %s: %s',
                function.__name__,
                traceback.format_exc(),
            )
            raise SystemExit(1)
    return logging_wrapper

@with_logging
def arpabet_guess():
    parser = argparse.ArgumentParser(description='Guess ARPABet pronunciation')
    parser.add_argument(
        'words',metavar='WORD',type=str,nargs="+",
        help="The words to guess",
    )
    arguments = parser.parse_args()
    from . import ipatoarpabet
    for word in arguments.words:
        print word
        for possible in ipatoarpabet.translate(word):
            print u'\t%s'%(possible,)
    
def _existing_filename( filename ):
    if not os.path.exists( filename ):
        raise argparse.ArgumentTypeError( '%s does not exist'%(filename,))
    return os.path.abspath( filename )
@with_logging
def code_to_words():
    from . import context,codetowords
    log = codetowords.log
    parser = base_arguments('Convert passed file names to guessed pronunciation')
    parser.add_argument(
        'files',metavar='FILE',type=_existing_filename,nargs="+",
        help="The files to process",
    )
    parser.add_argument(
        '--output',metavar='FILE',type=str,nargs=1,
        help="file into which to write the resulting statements (default to filename+'.dictation')",
        default=None,
    )
    arguments = parser.parse_args()
    working_context = context.Context( arguments.context )
    for filename in arguments.files:
        log.info('Translating: %s', filename )
        lines = open( filename ).readlines()
        translated = codetowords.codetowords( lines, working_context.dictionary_cache )
        composed = '\n'.join([
            '<s> %s </s>'%( ' '.join( line ))
            for line in translated
        ])
        if not arguments.output:
            context.twrite( filename + '.dictation', composed )
        else:
            with open( arguments.output,'a') as fh:
                fh.write( composed )
                fh.write( '\n' )
        
@with_logging
def missing_words():
    from . import context,codetowords,ipatoarpabet
    log = codetowords.log
    parser = base_arguments('Search for unknown words in python files')
    parser.add_argument(
        'files',metavar='FILE',type=_existing_filename,nargs="+",
        help="The files to process",
    )
    parser.add_argument(
        '--output',metavar='FILE',type=str,nargs=1,
        help="File into which to write the guessed pronunciation (custom dictionary, default stdout)",
        default=None,
    )
    arguments = parser.parse_args()
    working_context = context.Context( arguments.context )
    translated = []
    for filename in arguments.files:
        log.info('Translating: %s', filename )
        lines = open( filename ).readlines()
        translated.extend( codetowords.codetowords( lines, working_context.dictionary_cache ) )
    unmapped = set()
    all_words = set()
    for line in translated:
        all_words |= set(line)
    log.info( 'Checking %s words for transcriptions', len(all_words))
    transcriptions = working_context.transcriptions( sorted(all_words) )
    for word,arpa in transcriptions.items():
        if not arpa:
            unmapped.add( word )
    log.info( '%s words unmapped', len(unmapped))
    if arguments.output is None:
        fh = sys.stdout 
    else:
        fh = open( arguments.output, 'a' )
    try:
        for word in unmapped:
            possible = ipatoarpabet.translate( word )
            if isinstance( word, unicode ):
                word = word.encode('utf-8')
            for i,pron in enumerate( possible ):
                if isinstance( pron, unicode ):
                    pron = pron.encode('utf-8')
                fh.write('%s,%s\n'%(word,pron))
    finally:
        if fh is not sys.stdout:
            fh.close()
