from unittest import TestCase
import tempfile, shutil, os, time
from listener import pipeline,context,sourcedescription
HERE = os.path.dirname( __file__ )

class PipelineTests( TestCase ):
    HELLO_WORLD = os.path.join( HERE, 'fixtures','hello_world.wav' )
    pipeline = None
    def setUp( self ):
        self.workdir = tempfile.mkdtemp( 
            prefix='listener-', suffix='-test', dir='/dev/shm' 
        )
        self.context = context.Context(
            'default', directory=os.path.join(self.workdir,'config')
        )
    def tearDown( self ):
        shutil.rmtree( self.workdir, True ) # ignore errors
        if self.pipeline:
            self.pipeline.close()
    
    def test_source_description_parsing( self ):
        for url in [
            'alsa://hw:2,0',
            'file:///tmp/test/this.wav',
            #'file:///tmp/test/moo.ogg',
            'file:///tmp/test/moo.opus',
            'file:///tmp/test/moo.raw',
        ]:
            description = sourcedescription.SourceDescription( url )
            fragment = description.gst_fragment()
            assert fragment[-1] == '!', fragment 
    
    def test_pipeline_creation( self ):
        p = self.pipeline = pipeline.QueuePipeline( 
            context=self.context,
            source=self.HELLO_WORLD 
        )
        p.start_listening()
        t = time.time()
        TIMEOUT = t + 20
        result = None
        while time.time() < TIMEOUT:
            message = p.queue.get( True, TIMEOUT-time.time() )
            if message['type'] == 'final':
                result = message 
                break 
        assert result, "No result message received in 20s"
        assert result['text']
        assert 'hello world' in result['text'], result
    
    def test_pipeline_default_source_is_alsa( self ):
        self.pipeline = pipeline.QueuePipeline(context=self.context)
        assert self.pipeline.source.continuous
        fragment = self.pipeline.source.gst_fragment()
        assert 'alsasrc' in fragment, fragment
        
        self.pipeline.source = None 
        assert self.pipeline._source is None 
    
    
