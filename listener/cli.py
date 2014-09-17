"""Base argument parser for listener utilities"""
import argparse, logging, functools, os, sys, traceback, re
from . import context,ipatoarpabet,tokenizer,project
from ._bytes import as_bytes,as_unicode,bytes

def base_arguments(purpose):
    parser = argparse.ArgumentParser(description=purpose)
    parser.add_argument(
        '--context',type=bytes,
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
def context_keys():
    for key in context.Context.keys():
        print( key )
    
@with_logging
def arpabet_guess():
    parser = argparse.ArgumentParser(description='Guess ARPABet pronunciation')
    parser.add_argument(
        'words',metavar='WORD',type=bytes,nargs="+",
        help="The words to guess",
    )
    arguments = parser.parse_args()
    for word in arguments.words:
        print word
        for possible in ipatoarpabet.translate(word):
            print u'\t%s'%(possible,)
    
def _existing_filename( filename ):
    if not os.path.exists( filename ):
        raise argparse.ArgumentTypeError( '%s does not exist'%(filename,))
    return os.path.abspath( filename )
def _existing_directory( directory ):
    if not os.path.exists( directory ):
        raise argparse.ArgumentTypeError( '%s does not exist'%(directory,))
    if not os.path.isdir( directory ):
        raise argparse.ArgumentTypeError( '%s is not a directory'%(directory,))
    return os.path.abspath( directory )
@with_logging
def code_to_words():
    log = tokenizer.log
    parser = base_arguments('Convert passed file names to guessed pronunciation')
    parser.add_argument(
        'files',metavar='FILE',type=_existing_filename,nargs="+",
        help="The files to process",
    )
    parser.add_argument(
        '--output',metavar='FILE',type=bytes,
        help="file into which to write the resulting statements (default to filename+'.dictation')",
        default=None,
    )
    arguments = parser.parse_args()
    working_context = context.Context( arguments.context )
    tokens = tokenizer.Tokenizer( working_context.dictionary_cache )
    for filename in arguments.files:
        log.info('Translating: %s', filename )
        lines = open( filename ).readlines()
        translated = tokens( lines )
        composed = '\n'.join([
            u'<s> %s </s>'%( u' '.join( [x for x in line if x.strip()] ))
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
    parser = base_arguments('Search for unknown words in vcs project/directory')
    parser.add_argument(
        'directory',metavar='DIR',type=_existing_directory,
        help="The directory/vcs-checkout to process",
    )
    parser.add_argument(
        '--output',metavar='FILE',type=bytes,
        help="File into which to write the guessed pronunciation (custom dictionary, default stdout)",
        default=None,
    )
    parser.add_argument(
        '--filter', metavar='REGEX', type='bytes',
        help="Regex expression to use to filter the files (must match the filename with .match()), %r"%(
            project.DEFAULT_FILENAME_REGEX,
        ),
        default = project.DEFAULT_FILENAME_REGEX,
    )
    arguments = parser.parse_args()
    working_context = context.Context( arguments.context )
    files = project.get_filtered_files( arguments.directory, arguments.filter )
    translated = []
    for lines in project.iter_translated_lines( files, working_context ):
        translated.extend(lines)
    
    if arguments.output is None:
        fh = sys.stdout 
    else:
        fh = open( arguments.output, 'a' )
    try:
        for word,pron in project.iter_unmapped_words( translated, working_context ):
            fh.write('%s,%s\n'%(word,pron))
    finally:
        if fh is not sys.stdout:
            fh.close()

@with_logging
def import_words( ):
    """Import words from a csv-delimited ARPABet dictionary"""
    parser = base_arguments('Import words from a csv-delimited ARPABet dictionary')
    parser.add_argument(
        'file',metavar='FILE',type=_existing_filename,nargs="+",
        help="The file(s) to add to the context",
    )
    arguments = parser.parse_args()
    working_context = context.Context( arguments.context )
    for file in arguments.file:
        working_context.add_dictionary_file( file )

@with_logging
def delete_context():
    parser = base_arguments('Search for unknown words in python files')
    parser.add_argument(
        '-f', '--force',action='store_const', const=True,
        default=False,
        help="Force deletion even of the default context",
    )
    
    arguments = parser.parse_args()
    if arguments.context == 'default' and not arguments.force:
        raise RuntimeError( "You must specify --force to delete the default context" )
    working_context = context.Context( arguments.context )
    working_context.delete()
    
    
@with_logging
def context_from_project():
    log = tokenizer.log
    parser = base_arguments('Create a new listener context (or update an existing one) with guessed pronunciation from a vcs checkout')
    parser.add_argument(
        'directory',metavar='DIR',type=_existing_directory,
        help="The directory/vcs-checkout to process",
    )
    parser.add_argument(
        '--clean',action='store_const', const=True,
        default=False,
        help="If True, then wipe out previous ",
    )
    parser.add_argument(
        '-g','--guess-run-together',action='store_const', const=True,
        default=False,
        help="If True attempt to split apart run-together words into separate words",
    )
    arguments = parser.parse_args()
    if arguments.context == 'default':
        arguments.context = os.path.basename(os.path.abspath(arguments.directory))
    if arguments.context == 'default':
        raise RuntimeError( "You can't create a new default context" )
    working_context = context.Context( arguments.context )
    
    working_context.integrate_project( 
        arguments.directory, 
        clean=arguments.clean, 
        guess_run_together=arguments.guess_run_together
    )

@with_logging
def subset_dictionary(  ):
    """Create a subset dictionary from working context's dictionary
    
    This is a bit useless, so not recommended for use. Average person 
    has ~35,000 word vocabulary. The default dictionary is ~130,000
    words, way too large and full of lots of stuff you're not likely 
    to actually want to dictate.
    """
    log = logging.getLogger( 'subset' )
    parser = base_arguments('Create a dictionary subset of highest-frequency words from an NLTK corpus')
    parser.add_argument(
        '--corpus',type=bytes,default='webtext',
        help="NLTK corpus to download and process",
    )
    parser.add_argument(
        '--count',type=int,default=10000,
        help="Number of items to include in dictionary",
    )
    arguments = parser.parse_args()
    working_context = context.Context( arguments.context )
    import nltk, nltk.corpus
    nltk.download( arguments.corpus )
    corpus = getattr( nltk.corpus, arguments.corpus )
    total = corpus.words()
    log.info( '%s words in corpus', len(total))
    fd =nltk.FreqDist([
        as_unicode(w).lower()
        for w in total
        if w.isalnum()
    ])
    all_items = list(fd.iteritems())
    log.info( '%s distinct words', len(all_items))
    translations = working_context.dictionary_cache.have_words(
        *[x[0] for x in all_items[:int(arguments.count*1.5)]]
    )
    count = 0
    items = []
    for (word,frequency) in fd.iteritems():
        if translations.get( word ):
            count += 0
            for t in translations.get(word):
                items.append( (word,t))
            if count >= arguments.count:
                break 
    items.sort()
    for word,translation in items:
        print '%s\t%s'%(as_bytes(word),as_bytes(translation))

@with_logging
def qt_gui():
    parser = base_arguments('Run the qt-based listener GUI client')
    arguments = parser.parse_args()

    from . import qtgui
    return qtgui.main(arguments)

@with_logging
def dictionary_lookup():
    from . import context 
    import pprint
    parser = base_arguments('Lookup word pronunciation in dictionary')
    parser.add_argument(
        'words',metavar='WORD',type=bytes,nargs="+",
        help="The words to lookup",
    )
    arguments = parser.parse_args()
    working_context = context.Context( arguments.context )
    db = working_context.dictionary_cache
    pprint.pprint( db.have_words( *arguments.words ))
