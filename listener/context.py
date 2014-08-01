"""Creation of working directories for storing language models and training data"""
import os,shutil,tempfile,subprocess,json,time,glob
from functools import wraps
import logging
log = logging.getLogger( __name__ )

def one_shot( func ):
    """Only calculate once for each instance"""
    key = '_' + func.__name__
    @wraps( func )
    def cached( self ):
        if not hasattr( self, key ):
            setattr( self, key, func(self))
        return getattr( self, key )
    return cached

def base_config_directory(appname='listener'):
    """Produce a reasonable working directory in which to store our files"""
    config_dir = os.environ.get('XDG_CONFIG_HOME',os.path.expanduser('~/.config'))
    if os.path.exists( config_dir ):
        config_dir = os.path.join( config_dir, appname )
    else:
        config_dir = os.path.expanduser( '~/.%s'%(appname) )
    return config_dir 
def base_cache_directory(appname='listener'):
    cache_dir = os.environ.get( 'XDG_CACHE_HOME', os.path.expanduser('~/.cache'))
    cache_dir = os.path.join( cache_dir, appname )
    return cache_dir

def twrite( filename, data ):
    """Note: this is *not* thread/process safe!"""
    if isinstance( data, unicode ):
        data = data.encode('utf-8')
    elif not isinstance( data, bytes ):
        data = json.dumps( data )
        if isinstance( data, unicode ):
            data = data.encode('utf-8')
    with open( filename+ '~', 'wb' ) as fh:
        fh.write( data )
    os.rename( filename + '~', filename )
    return filename

class Context( object ):
    """Holds a dictation context from which we attempt to recognize
    
    TODO: need to allow the user to specify a specific alsa device
    to use for the dictation and playback.
    
    TODO: need to allow the user to specify levels for recording playback 
    independent of general desktop levels (KDE settings are not reliable)
    """
    def __init__( self, key, parent=None ):
        if not key.isalnum():
            raise ValueError( "Need an alpha-numeric name for the context" )
        self.key = key 
        if not os.path.exists( self.directory ):
            if not parent:
                self.initial_working_directory( )
            else:
                raise RuntimeError( """Don't have chained/parent contexts working yet""" )
    @property
    @one_shot
    def directory( self ):
        base = base_config_directory()
        return os.path.join( base, self.key )
    @property 
    @one_shot
    def language_model_directory( self ):
        return os.path.join( self.directory, 'lm' )
    @property 
    @one_shot
    def hmm_directory( self ):
        return os.path.join( self.directory, 'hmm' )
    @property 
    @one_shot
    def recording_directory( self ):
        return os.path.join( self.directory, 'recordings' )
    @property
    @one_shot
    def buffer_directory( self ):
        return os.path.join( self.directory, 'buffer' )
    @property
    @one_shot
    def language_model_file( self ):
        return os.path.join( self.language_model_directory, 'language_model.dmp' )
    @property 
    @one_shot
    def dictionary_file( self ):
        return os.path.join( self.language_model_directory, 'dictionary.dict' )
    
    def initial_working_directory( self,  ):
        """Create an initial working directory by cloning the pocketsphinx default models"""
        if not os.path.exists( self.directory ):
            os.makedirs( self.directory, 0700 )
        if not os.path.exists( self.language_model_directory ):
            os.makedirs( self.language_model_directory, 0700 )
        # Pull down the language model...
        archive = self.download_hmm_archive()
        tempdir = tempfile.mkdtemp( prefix='listener-', suffix='-unpack' )
        subprocess.check_call( [
            'tar', '-zxf',
            archive,
        ], cwd=tempdir )
        HMMs = [
            os.path.join( tempdir, 'hub4wsj_sc_8k'),
        ]
        DMPs = [
            '/usr/share/pocketsphinx/model/lm/en_US/hub4.5000.DMP',
        ]
        DICTIONARY = [
            '/usr/share/pocketsphinx/model/lm/en_US/cmu07a.dic',
        ]
        found = False
        for (dmp,dic,hmm) in zip(DMPs,DICTIONARY,HMMs):
            if os.path.exists( dmp ):
                shutil.copy( 
                    dmp, 
                    self.language_model_file,
                )
                shutil.copy(
                    dic,
                    self.dictionary_file,
                )
                shutil.copytree( 
                    hmm,
                    self.hmm_directory,
                )
                found = True 
        if not found:
            raise RuntimeError( 
                """We appear to be missing the ubuntu/debian package pocketsphinx-hmm-en-hub4wsj""" 
            )
        if not os.path.exists( self.recording_directory ):
            os.mkdir( self.recording_directory )
        if not os.path.exists( self.buffer_directory ):
            os.mkdir( self.buffer_directory )
        return self.directory

    SPHINXTRAIN_BIN = '/usr/lib/sphinxtrain/sphinxtrain'
    def acoustic_adaptation( self ):
        """Run acoustic adaptation on recorded data-set
        
        TODO: Likely should be machine and sound-source dependent so that 
        users can switch between devices?
        """
        log.info( 'Running acoustic adaptation' )
        training_records = list( self.training_records )
        
        fileid_file = os.path.join( self.hmm_directory, 'training.fileids' )
        twrite( fileid_file, '\n'.join([ record['filename'] for record in training_records]) )
        
        transcription_file = os.path.join( self.hmm_directory, 'training.transcription' )
        twrite( transcription_file, '\n'.join([
            '<s> %(transcription)s </s> (%(filename)s)'%record 
            for record in records 
        ]))
        
        
        for command in [
            [
                'sphinx_fe',
                    '-argfile', os.path.join( self.hmm_directory, 'feat.params'),
                    '-samprate', '16000',
                    '-c',fileid_file,
                    '-di',self.hmm_directory,
                    '-do',self.hmm_directory,
                    '-ei','wav',
                    '-eo','mfc',
                    '-mswav','yes',
            ],
            [
                os.path.join( self.SPHINXTRAIN_BIN,'bw'),
                '-hmmdir', self.hmm_directory,
                '-moddeffn', os.path.join( self.hmm_directory,'mdef.txt'),
                '-ts2cbfn','.semi.',
                '-feat','1s_c_d_dd',
                '-svspec','0-12/13-25/26-38',
                '-cmn','current',
                '-agc','none',
                # TODO: note that this is a very large file!
                '-dictfn',self.dictionary_file,
                '-ctlfn',fileid_file,
                '-lsnfn',transcription_file,
                '-accumdir', self.hmm_directory,
            ],
            
            [
                os.path.join( self.SPHINXTRAIN_BIN,'mllr_solve'),
                '-meanfn',os.path.join( self.hmm_directory, 'means' ),
                '-varfn',os.path.join( self.hmm_directory, 'variances'),
                '-outmllrfn','mllr_matrix',
                '-accumdir', self.hmm_directory,
            ],
        ]:
            log.info( 'Running: %s', command.join(' '))
            subprocess.check_call( command, cwd=self.hmm_directory )
    
    def download_url( self, url, filename ):
        """Download given URL to a local filename in our cache directory 
        
        returns the full filename
        """
        filename = os.path.basename( filename )
        target = os.path.join( base_cache_directory(), filename )
        if not os.path.exists( base_cache_directory()):
            os.makedirs( base_cache_directory() )
        if not os.path.exists( target ):
            log.warn( 'Downloading from %s', url )
            import urllib
            urllib.urlretrieve( url, target )
        return target
        
    # Only a root context should *likely* be doing acoustic training 
    # so it's likely we shouldn't have the acoustic training files 
    # present in the non-root contexts...
    # We may *also* want to move the user-specific HMM into 
    # its own directory (separate from the downloaded/base HMM)?
    
    HMM_URL = 'https://sourceforge.net/projects/cmusphinx/files/Acoustic%20and%20Language%20Models/US%20English%20HUB4WSJ%20Acoustic%20Model/hub4wsj_sc_8k.tar.gz/download'
    def download_hmm_archive( self ):
        return self.download_url( self.HMM_URL, 'hub4_wsj_language_model.tar.gz' )
    
    def transcription_filename( self, transcription ):
        name = os.path.join( 
            self.recording_directory, 
            ''.join([ c if c.isalnum() else '_' for c in transcription ]) + '.wav'
        )
        return name
    def add_training_data( self, recording, transcription, private=False ):
        name = self.transcription_filename( transcription )
        if os.path.exists( name ):
            raise RuntimeError( 'Delete the file %s before calling add_training_data' )
        shutil.copy( recording, name )
        description = name + '.json'
        record = { 
            'filename': name, 'transcription': transcription, 'timestamp': time.time(),
            'private': private,
        }
        twrite( description, record )
        return record
    def remove_training_data( self, transcription ):
        name = self.transcription_filename( transcription )
        for n in (name+'.json', name ):
            try:
                os.remove( name + '.json' )
            except (IOError,OSError) as err:
                pass
    def training_records( self, private=True ):
        for json_file in glob.glob( os.path.join( self.recording_directory, '*.json' )):
            try:
                record = json.loads( open( json_file ).read())
                if os.path.exists( record['filename'] ):
                    if private or not record['private']:
                        yield record 
                else:
                    log.error( 'Training record in %s does not have accompanying data', json_file )
                    os.rename( json_file, json_file+'.stale' )
            except Exception as err:
                pass 
    
    def rawplay(self, filename):
        """Play the given filename 
        
        filename -- either an absolute path to the filename or 
            a "basename" for the filename present in our recordings 
            directory 
        """
        log.info( 'Playing raw file: %s', filename )
        if os.path.basename(filename) == filename:
            filename = os.path.join( self.buffer_directory, filename)
        if not os.path.exists( filename ):
            log.info( 'No such file: %s', filename )
            return 
        # TODO: this should *not* be running in the GUI thread!
        # the context should be running out-of-process and the 
        # playback should be a separate operation
        subprocess.Popen( [
            'gst-launch',
            'filesrc','location=%s'%(
                filename,
            ),'!',
            'audioparse',
                'width=16','depth=16',
                'signed=true',
                'rate=8000',
                'channels=1',
                '!',
            'audiorate','!',
            'audioconvert','!',
            'alsasink'
        ]).communicate()
        log.info( 'Finished playing' )
