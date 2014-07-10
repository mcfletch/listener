"""The GStreamer PocketSphinx tutorial

Copyright (c) 2008 Carnegie Mellon University.

You may modify and redistribute this file under the same terms as
the CMU Sphinx system.  See 
http://cmusphinx.sourceforge.net/html/LICENSE for more information.
"""
import sys, os, shutil, logging
import pygst
pygst.require("0.10")
import gst
import gobject
import Queue
log = logging.getLogger( __name__ )
HERE = os.path.dirname( __file__ )

def create_working_directory( directory ):
    os.makedirs( directory, 0700 )
    model_dir =os.path.join(directory,'lm') 
    os.mkdir( model_dir )
    shutil.copy( 
        '/usr/share/pocketsphinx/model/lm/wsj/wlist5o.3e-7.vp.tg.lm.DMP', 
        os.path.join(model_dir,'language_model.dmp')
    )
    shutil.copy(
        '/usr/share/pocketsphinx/model/lm/wsj/wlist5o.dic',
        os.path.join(model_dir,'dictionary.dic')
    )
    return directory

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
    def __init__( self, working_directory ):
        """Initialize our pipeline using the given working-directory"""
        self.working_directory = working_directory
        if not os.path.exists( working_directory ):
            create_working_directory( working_directory )
    
    _queue = None 
    @property 
    def queue( self ):
        if self._queue is None:
            self._queue = Queue.Queue()
        return self._queue

    @property
    def pipeline_command( self ): 
        # TODO: *also* save to in-memory file(s) for acoustic training
        # and re-processing by different contextual language models
        language_model = os.path.join( self.working_directory, 'lm', 'language_model.dmp' )
        dictionary = os.path.join( self.working_directory, 'lm', 'dictionary.dic' )
        # TODO: allow for swapping in different pocket-sphinx contexts against the same 
        # stream, potentially having multiple pocket-sphinxs running at the same time
        # TODO: add an audio pre-processing stage to filter out background noise and 
        # require a clear signal before cutting in
        return [
                'alsasrc', 'name=source', '!',
                'audioconvert', '!',
                'audioresample', '!',
                'vader','name=vader', 'auto-threshold=true', '!',
                'pocketsphinx',
                    'name=sphinx', 
                    'lm="%s"'%(language_model,),
                    'dict="%s"'%(dictionary,),
                    '!',
                'fakesink',
            ]

    _pipeline = None
    @property 
    def pipeline( self ):
        if self._pipeline is None:
            gobject.threads_init()
            language_model = os.path.join( self.working_directory, 'lm', 'language_model.dmp' )
            dictionary = os.path.join( self.working_directory, 'dictionary.dic' )
            
            command = " ".join( self.pipeline_command )
            log.info( 'Pipeline: %s', command )
            self._pipeline = gst.parse_launch(command)

            sphinx = self._pipeline.get_by_name( 'sphinx' )
            sphinx.connect('partial_result', self.sphinx_partial_result)
            sphinx.connect('result', self.sphinx_result)
            sphinx.set_property('configured', True)

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
    
    def update_language_model( self, source ):
        """Update our language model from a given source
        
            http://cmusphinx.sourceforge.net/wiki/tutoriallm
        """
        self.stop_listening()
        sphinx.set_property('configured', False)
        sphinx.set_property('lm', source)
        sphinx.set_property('configured', True)
        self.start_listening()
        
    def sphinx_partial_result(self, sphinx, text, uttid):
        """Forward partial result signals via our queue"""
        self.queue.put( {
            'type':'partial',
            'text': text,
            'uttid': uttid,
        })
    def sphinx_result(self, asr, text, uttid):
        """Forward result signals via our queue"""
        self.queue.put( {
            'type':'final',
            'text': text,
            'uttid': uttid,
        })

def main():
    """Command-line script to run the pipeline"""
    config_dir = os.environ.get('XDG_CONFIG_HOME',os.path.expanduser('~/.config'))
    if os.path.exists( config_dir ):
        config_dir = os.path.join( config_dir, 'listener' )
    else:
        config_dir = os.path.expanduser( '~/.listener' )
    if not os.path.exists( config_dir ):
        config_dir = create_working_directory( config_dir )
    pipe = Pipeline(config_dir)
    pipe.start_listening()
    while True:
        try:
            result = pipe.queue.get( True, 2 )
        except Queue.Empty as err:
            pass 
        else:
            print( '%(type) 7s #%(uttid)05s %(text)s'%result )
            if result['type'] == 'final':
                print()

