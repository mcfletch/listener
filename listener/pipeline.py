"""The GStreamer PocketSphinx tutorial

Copyright (c) 2008 Carnegie Mellon University.

You may modify and redistribute this file under the same terms as
the CMU Sphinx system.  See 
http://cmusphinx.sourceforge.net/html/LICENSE for more information.
"""
import sys, os, shutil, logging, pprint,subprocess, urlparse
import pygst
pygst.require("0.10")
import gst
import gobject
import Queue
from . import context
from . import sourcedescription
log = logging.getLogger( __name__ )
HERE = os.path.dirname( __file__ )

class Pipeline( object ):
    """Holds the PocketSphinx Pipeline we'll use for recognition
    
    The idea here is that the Gstreamer/PocketSphinx back-end is isolated from 
    the GUI code, with the idea that we might be able to add in another backend 
    at some point in the future...
    
    Here's the gst-inspect from the pocketsphinx component:

    Element Properties:
      hmm                 : Directory containing acoustic model parameters
                            flags: readable, writable
                            String. Default: "/usr/share/pocketsphinx/model/hmm/wsj1"
      lm                  : Language model file
                            flags: readable, writable
                            String. Default: "/usr/share/pocketsphinx/model/lm/wsj/wlist5o.3e-7.vp.tg.lm.DMP"
      lmctl               : Language model control file (for class LMs)
                            flags: readable, writable
                            String. Default: null
      lmname              : Language model name (to select LMs from lmctl)
                            flags: readable, writable
                            String. Default: "default"
      dict                : Dictionary File
                            flags: readable, writable
                            String. Default: "/usr/share/pocketsphinx/model/lm/wsj/wlist5o.dic"
      fsg                 : Finite state grammar file
                            flags: readable, writable
                            String. Default: null
      fsg-model           : Finite state grammar object (fsg_model_t *)
                            flags: writable
                            Pointer. Write only
      fwdflat             : Enable Flat Lexicon Search
                            flags: readable, writable
                            Boolean. Default: false
      bestpath            : Enable Graph Search
                            flags: readable, writable
                            Boolean. Default: false
      maxhmmpf            : Maximum number of HMMs searched per frame
                            flags: readable, writable
                            Integer. Range: 1 - 100000 Default: 1000 
      maxwpf              : Maximum number of words searched per frame
                            flags: readable, writable
                            Integer. Range: 1 - 100000 Default: 10 
      dsratio             : Evaluate acoustic model every N frames
                            flags: readable, writable
                            Integer. Range: 1 - 10 Default: 1 
      latdir              : Output Directory for Lattices
                            flags: readable, writable
                            String. Default: null
      lattice             : Word lattice object for most recent result
                            flags: readable
                            Boxed pointer of type "PSLattice"
      decoder             : The underlying decoder
                            flags: readable
                            Boxed pointer of type "PSDecoder"
      configured          : Set this to finalize configuration
                            flags: readable, writable
                            Boolean. Default: false
    
    Adaptation/Training still needs to be looked into...

        http://cmusphinx.sourceforge.net/wiki/tutorialadapt

    """
    def __init__( self, context, audio_context=None, source=None ):
        """Initialize our pipeline using the given working-directory"""
        self.context = context
        self.audio_context = audio_context or context.audio_context()
        if os.path.exists( context.buffer_directory ):
            for filename in os.listdir( context.buffer_directory ):
                os.remove( os.path.join( context.buffer_directory, filename ))
        else:
            os.makedirs( self.context.buffer_directory )
        self.existing_utterances = set()
        if source is not None:
            self.source = source
    
    _source = None
    @property 
    def source( self ):
        if self._source is None:
            self._source = sourcedescription.SourceDescription( 
                'alsa://%s'%(self.audio_context.settings['input_device'])
            )
        return self._source
    
    @source.setter
    def source( self, source ):
        """Set our source from a string in URL format
        
        alsa://hw:2,0
        file:///path/to/file.raw
        file:///path/to/file.opus
        file:///path/to/file.wav
        
        From the source we will decide how to play the audio 
        file in order to get the audio into the format we need,
        performing resampling and the like.
        """
        if source:
            self._source = sourcedescription.SourceDescription( 
                source 
            )
            # validate that we can calculate a gstreamer fragment from it...
            self._source.gst_fragment()
        else:
            self._source = None 

    @property
    def pipeline_command( self ): 
        # TODO: *also* save to in-memory file(s) for acoustic training
        # and re-processing by different contextual language models
        # TODO: allow for swapping in different pocket-sphinx contexts against the same 
        # stream, potentially having multiple pocket-sphinxs running at the same time
        # TODO: add an audio pre-processing stage to filter out background noise and 
        # require a clear signal before cutting in
        return self.source.gst_fragment() + [
                'audioconvert', '!',
                'audioresample', '!',
                'level', 
                    'name=monitor', 
                    'interval=%s'%int(.01 * 10.**9),
                    'message=true','!',
                'audio/x-raw-int,width=16,depth=16,channels=1,rate=8000', 
                '!',
                'tee', 'name=tee', '!',
                'vader',
                    'name=vader', 
                    'auto-threshold=true', 
                    'dump-dir=%s'%(self.context.buffer_directory,),
                    '!',
                'pocketsphinx',
                    'name=sphinx', 
                    'nbest-size=10',
                    'lm="%s"'%(self.context.language_model_file,),
                    'dict="%s"'%(self.context.dictionary_file,), '!',
                'fakesink',
            ]

    _pipeline = None
    @property 
    def pipeline( self ):
        if self._pipeline is None:
            gobject.threads_init()
            
            command = " ".join( self.pipeline_command )
            log.info( 'Pipeline: %s', command )
            self._pipeline = gst.parse_launch(command)

            sphinx = self._pipeline.get_by_name( 'sphinx' )
            sphinx.connect('partial_result', self.sphinx_partial_result)
            sphinx.connect('result', self.sphinx_result)
            sphinx.set_property('configured', True)
            
            self.monitor = self._pipeline.get_by_name( 'monitor' )
            
            bus = self._pipeline.get_bus()
            bus.add_signal_watch()
            bus.connect( 'message', self.on_level )
            
            self.pipeline.set_state(gst.STATE_PAUSED)

        return self._pipeline
    
    @property 
    def sphinx( self ):
        return self.pipeline.get_by_name('sphinx')
    
    def start_listening( self ):
        """Start Listening for spoken input"""
        self.pipeline.set_state(gst.STATE_PLAYING)
    def pause_listening( self ):
        """Pause listening"""
        vader = self.pipeline.get_by_name('vad')
        vader.set_property('silent', True)
    def stop_listening( self ):
        """Stop listening"""
        self.pipeline.set_state(gst.STATE_PAUSED)
    
    def close( self ):
        """Close and cleanup our pipeline entirely"""
        if self._pipeline:
            self.stop_listening()
        self._pipeline = None
    
    def update_language_model( self, source ):
        """Update our language model from a given source
        
            http://cmusphinx.sourceforge.net/wiki/tutoriallm
        """
        self.stop_listening()
        sphinx.set_property('configured', False)
        sphinx.set_property('lm', source)
        sphinx.set_property('configured', True)
        self.start_listening()
    
    def on_level( self, bus, message ):
        """Level message was received"""
        if message.src == self.monitor and message.type==gst.MESSAGE_ELEMENT:
            self.send( {
                'type':'level',
                'level': message.structure['rms'][0],
            })
    
    def sphinx_partial_result(self, sphinx, text, uttid):
        """Forward partial result signals via our queue"""
        self.send( {
            'type':'partial',
            'text': text,
            'uttid': uttid,
            'nbest': None,
        })
    def sphinx_result(self, asr, text, uttid):
        """Forward result signals via our send() method"""
        new = []
        try:
            for filename in os.listdir( self.context.buffer_directory ):
                if filename not in self.existing_utterances:
                    self.existing_utterances.add( filename )
                    new.append( filename )
        except (OSError,IOError) as err:
            log.warning( 'Unable to read buffer directory?' )
            pass 
        self.send( {
            'type':'final',
            'text': text,
            'uttid': uttid,
            'nbest': getattr( self.sphinx, 'nbest',(text,)),
            'files': new,
        })
    def send( self, message ):
        raise NotImplemented( 'Must have a send method on pipelines' )

class QueuePipeline( Pipeline ):
    """Sub-class of Pipeline using Python Queues for comm"""
    _queue = None 
    @property 
    def queue( self ):
        if self._queue is None:
            self._queue = Queue.Queue()
        return self._queue
    def send( self, message ):
        self.queue.put( message )

def main():
    """Command-line script to run the pipeline"""
    context = context.Context( 'default' )
    pipe = QueuePipeline(context)
    pipe.start_listening()
    while True:
        try:
            result = pipe.queue.get( True, 2 )
        except Queue.Empty as err:
            pass 
        else:
            if result['type'] == 'final':
                pprint.pprint( result )
                print()
            else:
                print( '%(type) 7s #%(uttid)05s %(text)s'%result )
                
def rawplay():
    """Play file from the default context (or an absolute pathname)"""
    context = context.Context( 'default' )
    filename = sys.argv[1]
    return context.rawplay( filename )
