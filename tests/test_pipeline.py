from unittest import TestCase
import tempfile, shutil, os
from listener import pipeline,context

class PipelineTests( TestCase ):
    def setUp( self ):
        self.workdir = tempfile.mkdtemp( 
            prefix='listener-', suffix='-test', dir='/dev/shm' 
        )
        self.context = context.Context(
            'default', directory=os.path.join(self.workdir,'config')
        )
    def tearDown( self ):
        shutil.rmtree( self.workdir, True ) # ignore errors
    
    def test_source_description_parsing( self ):
        for url in [
            'alsa://hw:2,0',
            'file:///tmp/test/this.wav',
            #'file:///tmp/test/moo.ogg',
            'file:///tmp/test/moo.opus',
            'file:///tmp/test/moo.raw',
        ]:
            description = pipeline.SourceDescription( url )
            fragment = description.gstreamer_fragment()
            assert fragment[-1] == '!', fragment 
    
