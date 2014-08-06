"""Base argument parser for listener utilities"""
import argparse, logging, functools, os, sys, traceback, subprocess
from . import context,codetowords,ipatoarpabet
from ._bytes import as_bytes,as_unicode,unicode,bytes

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
    log = codetowords.log
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
    log = codetowords.log
    parser = base_arguments('Search for unknown words in python files')
    parser.add_argument(
        'files',metavar='FILE',type=_existing_filename,nargs="+",
        help="The files to process",
    )
    parser.add_argument(
        '--output',metavar='FILE',type=bytes,
        help="File into which to write the guessed pronunciation (custom dictionary, default stdout)",
        default=None,
    )
    arguments = parser.parse_args()
    working_context = context.Context( arguments.context )
    translated = []
    for lines in iter_translated_lines( arguments.files, working_context ):
        translated.extend(lines)
    
    if arguments.output is None:
        fh = sys.stdout 
    else:
        fh = open( arguments.output, 'a' )
    try:
        for word,pron in iter_unmapped_words( translated ):
            fh.write('%s,%s\n'%(word,pron))
    finally:
        if fh is not sys.stdout:
            fh.close()

def iter_translated_lines( files, working_context ):
    log = codetowords.log
    for filename in files:
        log.info('Translating: %s', filename )
        lines = open( filename ).readlines()
        try:
            yield codetowords.codetowords( 
                lines, working_context.dictionary_cache 
            )
        except Exception as err:
            log.error( 'Unable to translate: %s\n%s', filename, traceback.format_exc())
            continue 
            
def iter_unmapped_words( translated, working_context ):
    log = codetowords.log
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
    for word in unmapped:
        possible = ipatoarpabet.translate( word )
        for i,pron in enumerate( possible ):
            yield word,pron
            
def get_python_files( directory ):
    """Given a vcs directory, list the checked-in python files"""
    if os.path.exists( os.path.join( directory,'.git')):
        files = subprocess.check_output(
            'git ls-files |grep "[.]py"',
            shell=True,
        )
        return [ os.path.join(directory,f) for f in files.splitlines() if f.strip()]
    # TODO: other vcs's and default to os.walkdir()
    raise RuntimeError( 'Currently only handle git projects' )

@with_logging
def context_from_project():
    log = codetowords.log
    parser = base_arguments('Search for unknown words in python files')
    parser.add_argument(
        'directory',metavar='DIR',type=_existing_directory,
        help="The files to process",
    )
    parser.add_argument(
        '--clean',action='store_const', const=True,
        default=False,
        help="If True, then wipe out previous ",
    )
    arguments = parser.parse_args()
    working_context = context.Context( arguments.context )
    files = get_python_files( arguments.directory )
    all_lines = []
    with open( working_context.custom_language_model,['a','w'][bool(arguments.clean)]) as fh:
        for translated in iter_translated_lines( files, working_context ):
            all_lines.extend(translated)
            composed = '\n'.join([
                '<s> %s </s>'%( ' '.join( [
                    as_bytes(word)
                    for word in line 
                ]))
                for line in translated
            ])
            fh.write( composed )
            fh.write( '\n' )
    for word,pron in iter_unmapped_words( all_lines, working_context ):
        log.info( 'Adding word: %r -> %r', word,pron )
        working_context.add_custom_word( as_unicode(word),as_unicode(pron) )

    working_context.regenerate_language_model()

@with_logging
def qt_gui():
    parser = base_arguments('Run the qt-based listener GUI client')
    arguments = parser.parse_args()

    from . import qtgui
    app = qtgui.QtGui.QApplication(sys.argv)
    MainWindow = qtgui.ListenerMain(arguments=arguments)
    MainWindow.show()
    
    app.exec_()

if __name__ == "__main__":
    main()