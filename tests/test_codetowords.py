from unittest import TestCase
import tempfile, shutil, os, time
from listener import codetowords,context
HERE = os.path.dirname( __file__ )

class CodeToWordsTests( TestCase ):
    def setUp( self ):
        self.workdir = tempfile.mkdtemp( 
            prefix='listener-', suffix='-test', dir='/dev/shm' 
        )
        self.context = context.Context('default')

    def tearDown( self ):
        shutil.rmtree( self.workdir, True ) # ignore errors
    def test_ops_parsed( self ):
        assert '[' in codetowords.OP_NAMES, codetowords.OP_NAMES
        assert codetowords.OP_NAMES['['] == '[open-bracket'
