"""Creation of working directories for storing language models and training data"""
import os,shutil,tempfile,subprocess,json,time,glob
import logging
from .oneshot import one_shot
from ._bytes import as_unicode,as_bytes
log = logging.getLogger( __name__ )
HERE = os.path.dirname( __file__ )

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
        data = as_bytes( data )
    elif not isinstance( data, bytes ):
        data = json.dumps( data, indent=2, sort_keys=True )
        if isinstance( data, unicode ):
            data = data.encode('utf-8')
    directory = os.path.dirname( filename )
    if not os.path.exists( directory ):
        os.makedirs( directory )
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
    TEMPLATE_FILES = [
        os.path.join( HERE, 'punctuation.csv' ),
        os.path.join( HERE, 'meta-commands.csv' ),
        os.path.join( HERE, 'commonshortforms.csv' ),
    ]
    
    def __init__( self, key, parent=None, directory=None ):
        if not key.isalnum():
            raise ValueError( "Need an alpha-numeric name for the context" )
        self.key = key 
        if directory is not None:
            self.directory = directory
        if not os.path.exists( self.directory ):
            if not parent:
                self.initial_working_directory( )
            else:
                raise RuntimeError( """Don't have chained/parent contexts working yet""" )
    @classmethod 
    def keys( self ):
        """Return the set of contexts currently available"""
        return [
            os.path.basename(directory)
            for directory in glob.glob( os.path.join( base_config_directory(), '*' ))
        ]
    
    
    @one_shot
    def directory( self ):
        base = base_config_directory()
        return os.path.join( base, self.key )
    @one_shot
    def language_model_directory( self ):
        return os.path.join( self.directory, 'lm' )
    @one_shot
    def hmm_directory( self ):
        return os.path.join( self.directory, 'hmm' )
    @one_shot
    def audio_context_directory( self ):
        return os.path.join( self.directory, 'audiocontexts' )
    @one_shot
    def buffer_directory( self ):
        return os.path.join( self.directory, 'buffer' )
    @one_shot
    def language_model_file( self ):
        return os.path.join( self.language_model_directory, 'language_model.dmp' )
    @one_shot
    def dictionary_file( self ):
        return os.path.join( self.language_model_directory, 'dictionary.dict' )
    @one_shot
    def base_dictionary_file( self ):
        return os.path.join( self.language_model_directory, 'base.dict' )
    @one_shot
    def custom_dictionary_file( self ):
        return os.path.join( self.language_model_directory, 'custom.dict' )
    @one_shot
    def custom_language_model( self ):
        return os.path.join( self.language_model_directory, 'statements.txt' )
    
    def available_alsa_devices( self ):
        """Report the description,id for all available alsa devices"""
        from . import alsadevices
        return {
            'input': alsadevices.get_inputs(),
            'output': alsadevices.get_outputs(),
        }
    
    def audio_context( self, key=None ):
        """Should only be done on root context..."""
        key = key or 'default'
        return AudioContext( self, key )
    
    def initial_working_directory( self,  ):
        """Create an initial working directory by cloning the pocketsphinx default models"""
        if not os.path.exists( self.directory ):
            os.makedirs( self.directory, 0700 )
        if not os.path.exists( self.language_model_directory ):
            os.makedirs( self.language_model_directory, 0700 )
        # Pull down the language model...
        archive = self.download_hmm_archive()
        tempdir = tempfile.mkdtemp( prefix='listener-', suffix='-unpack' )
        try:
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
                    shutil.copy(
                        dic,
                        self.base_dictionary_file,
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
            # this should likely be a mechanism to allow the user 
            # to mix-in various utility dictionaries, but these
            # are *so* common we likely always need them...
            for template in self.TEMPLATE_FILES:
                self.copy_template_to_dictionary(
                    template,
                    self.custom_dictionary_file,
                )
            self.copy_template_statements()
            if not os.path.exists( self.buffer_directory ):
                os.mkdir( self.buffer_directory )
            return self.directory
        finally:
            shutil.rmtree( tempdir )
    
    def iter_template_words( self, template, separator=','):
        lines = [
            line.split(separator,1)
            for line in open( template ).read().splitlines()
            if line.strip()
        ]
        for line in lines:
            yield line
    
    def copy_template_to_dictionary( self, template, dictionary, separator=','):
        written_counts = {}
        with open( dictionary, 'a') as fh:
            words = []
            for line in self.iter_template_words( template, separator ):
                try:
                    count = written_counts.get( line[0],0)
                    count += 1
                    written_counts[line[0]] = count
                    if count != 1:
                        line[0] = '%s(%s)'%(line[0],count)
                    fh.write( '%s\t%s\n'%tuple(line))
                except Exception as err:
                    err.args += (line,)
                    raise
    def copy_template_statements(self):
        words = set()
        for template in self.TEMPLATE_FILES:
            for line in self.iter_template_words( 
                template, 
            ):
                words.add(line[0])
        self.add_statements( words )

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
        
    HMM_URL = 'https://sourceforge.net/projects/cmusphinx/files/Acoustic%20and%20Language%20Models/US%20English%20HUB4WSJ%20Acoustic%20Model/hub4wsj_sc_8k.tar.gz/download'
    def download_hmm_archive( self ):
        return self.download_url( self.HMM_URL, 'hub4_wsj_language_model.tar.gz' )
    
    CLM_TK_URL = "https://downloads.sourceforge.net/project/cmusphinx/cmuclmtk/0.7/cmuclmtk-0.7.tar.gz?r=&ts=1407260026&use_mirror=hivelocity"
    def download_langauge_model_tools( self ):
        """Download the CMU CLM Toolkit
        
        Why isn't this packaged for Ubuntu, I don't know...
        """
        return self.download_url( self.CLM_TK_URL, 'cmuclmtk-0.7.tar.gz' )
    
    def rawplay(self, filename):
        """Play the given filename 
        
        filename -- either an absolute path to the filename or 
            a "basename" for the filename present in our recordings 
            directory 
        
        TODO: this doesn't belong on the context... not sure where it should
        be
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
                #'device=hw:2,0', # from a setting somewhere
        ]).communicate()
        log.info( 'Finished playing' )

    @one_shot
    def dictionary_cache( self ):
        from . import dictionarycache, ipatoarpabet
        return dictionarycache.DictionaryDB( self )
        
    def transcriptions( self, words, guess=False ):
        """Retrieve (known/guessed) transcriptions for the given words
        
        TODO: we should actually *test* the guesses by updating the 
        language model and seeing which guess matches when processing 
        the audio being corrected... that will need quite a bit of work,
        as we'll need to space-pad the files, generate temporary lms and 
        process the audio N times... that likely needs to be 
        offline/hidden/background processing
        """
        cached = self.dictionary_cache.have_words( *words )
        if guess:
            for word in words:
                if not cached.get( word ):
                    from . import ipatoarpabet
                    cached[word] = ipatoarpabet.translate( word )
        return cached
    
    def add_custom_word( self, word, arpabet ):
        """Add a custom word to our dictionary"""
        word = as_unicode(word).lower()
        arpabet = as_unicode(arpabet).upper()
        with open( self.custom_dictionary_file, 'a' ) as fh:
            fh.write( '%s\t%s\n'%( as_bytes(word), as_bytes(arpabet) ))
        self.dictionary_cache.add_dictionary_iterable([(word,arpabet)])
    
    LM_TOOLS_PREFIX = os.path.expanduser( '~/.local/lib/listener/cmutk' )
    LM_BIN_DIRECTORY = os.path.join( LM_TOOLS_PREFIX, 'bin' )
    # Language model updates...
    def ensure_lm_tools( self ):
        if os.path.exists( os.path.join( self.LM_BIN_DIRECTORY, 'idngram2lm') ):
            log.info( 'Installed' )
            return
        # okay, so need to download, unpack and build...
        log.warn( 'Need to get the language model tools to compile new model' )
        archive = self.download_langauge_model_tools()
        build = tempfile.mkdtemp( prefix='listener-cmu-', suffix='-build' )
        try:
            expected_dir = 'cmuclmtk-0.7'
            subprocess.check_call( [
                'tar', '-zxf', archive 
            ], cwd=build)
            expected = os.path.join( build, expected_dir )
            if not os.path.exists( expected ):
                raise RuntimeError( "Didn't unpack the expected directory %s from %s: following directories created %s"%(
                    expected_dir,
                    archive,
                    os.listdir(build) )
                )
            subprocess.check_call([
                os.path.join(expected,'configure'), '--prefix=%s'%(os.path.abspath( self.LM_TOOLS_PREFIX )),
            ], cwd=expected)
            subprocess.check_call([
                'make', 'install',
            ], cwd=expected)
        finally:
            shutil.rmtree( build )
    
    
    
    def add_statements( self, texts ):
        """Add a bit of text to our language model description"""
        with open( self.custom_language_model, 'a' ) as fh:
            # TODO: sanitize the text...
            for text in texts:
                content = '<s> %s </s>\n'%( as_bytes(text), )
                fh.write( content )
    
    def regenerate_language_model( self ):
        """Regenerate our language model"""
        self.ensure_lm_tools()
        
        subprocess.check_call(
            'cat %s %s > %s'%(
                self.base_dictionary_file, 
                self.custom_dictionary_file,
                self.dictionary_file,
            ),
            shell=True,
        )
        bin = self.LM_BIN_DIRECTORY
        subprocess.check_call(
            '%s < %s | %s > %s'%(
                os.path.join( bin, 'text2wfreq' ),
                self.custom_language_model,
                os.path.join( bin, 'wfreq2vocab' ),
                self.custom_language_model+'.vocab',
            ),
            shell=True,
        )
        subprocess.check_call(
            '%s -vocab %s -idngram %s < %s'%(
                os.path.join( bin, 'text2idngram' ),
                self.custom_language_model+'.vocab',
                self.custom_language_model+'.idngram',
                self.custom_language_model,
            ),
            shell=True,
        )
        subprocess.check_call(
            '%s -vocab_type 0 -idngram %s -vocab %s -arpa %s'%(
                os.path.join( bin, 'idngram2lm' ),
                self.custom_language_model+'.idngram',
                self.custom_language_model+'.vocab',
                self.custom_language_model+'.arpa',
            ),
            shell=True,
        )
        subprocess.check_call(
            'sphinx_lm_convert -i %s -o %s'%(
                self.custom_language_model+'.arpa',
                self.language_model_file + '~',
            ),
            shell=True,
        )
        os.rename( self.language_model_file + '~', self.language_model_file )
    
    def delete( self ):
        """Delete our directory and all children"""
        shutil.rmtree( self.directory, True )

class AudioContext( object ):
    """Audio/hardware/user context used to do acoustic adaptation
    
    TODO: this needs to be keyed to *something*, likely the alsa 
    device, and maybe the machine... and maybe the abstract "environment"
    in which dictation is occurring...
    """
    def __init__( self, root_context, key=None ):
        """Initialize the audio context connected to a root context"""
        self.context = root_context
        self.key = key or 'default'
    @one_shot
    def base_config_directory( self ):
        return os.path.join( self.context.audio_context_directory, self.key )
    @one_shot
    def recording_directory( self ):
        return os.path.join( self.base_config_directory, 'recordings' )
    @one_shot
    def settings_file( self ):
        return os.path.join( self.base_config_directory, 'settings.json' )
    def save_settings( self ):
        content = json.dumps( self.settings, indent=2, sort_keys=True )
        twrite( self.settings_file, content )
    @one_shot
    def settings( self ):
        if os.path.exists( self.settings_file ):
            content = json.loads( open( self.settings_file ).read() )
        else:
            content = {
                'input_device': 'default',
                'output_device': 'default',
            }
        return content
    # We may *also* want to move the user-specific HMM into 
    # its own directory (separate from the downloaded/base HMM)?
    
    SPHINXTRAIN_BIN = '/usr/lib/sphinxtrain/sphinxtrain'
    def acoustic_adaptation( self ):
        """Run acoustic adaptation on recorded data-set
        
        TODO: Likely should be machine and sound-source dependent so that 
        users can switch between devices?
        """
        log.info( 'Running acoustic adaptation' )
        training_records = list( self.training_records )
        
        fileid_file = os.path.join( self.context.hmm_directory, 'training.fileids' )
        twrite( fileid_file, '\n'.join([ record['filename'] for record in training_records]) )
        
        transcription_file = os.path.join( self.context.hmm_directory, 'training.transcription' )
        twrite( transcription_file, '\n'.join([
            '<s> %(transcription)s </s> (%(filename)s)'%record 
            for record in training_records 
        ]))
        
        for command in [
            [
                'sphinx_fe',
                    '-argfile', os.path.join( self.context.hmm_directory, 'feat.params'),
                    '-samprate', '16000',
                    '-c',fileid_file,
                    '-di',self.context.hmm_directory,
                    '-do',self.context.hmm_directory,
                    '-ei','wav',
                    '-eo','mfc',
                    '-mswav','yes',
            ],
            [
                os.path.join( self.SPHINXTRAIN_BIN,'bw'),
                '-hmmdir', self.context.hmm_directory,
                '-moddeffn', os.path.join( self.context.hmm_directory,'mdef.txt'),
                '-ts2cbfn','.semi.',
                '-feat','1s_c_d_dd',
                '-svspec','0-12/13-25/26-38',
                '-cmn','current',
                '-agc','none',
                # TODO: note that this is a very large file!
                '-dictfn',self.context.dictionary_file,
                '-ctlfn',fileid_file,
                '-lsnfn',transcription_file,
                '-accumdir', self.context.hmm_directory,
            ],
            
            [
                os.path.join( self.SPHINXTRAIN_BIN,'mllr_solve'),
                '-meanfn',os.path.join( self.context.hmm_directory, 'means' ),
                '-varfn',os.path.join( self.context.hmm_directory, 'variances'),
                '-outmllrfn','mllr_matrix',
                '-accumdir', self.context.hmm_directory,
            ],
        ]:
            log.info( 'Running: %s', command.join(' '))
            subprocess.check_call( command, cwd=self.context.hmm_directory )
    
    def add_training_data( self, recording, transcription, private=False ):
        name = self.transcription_filename( transcription )
        shutil.copy( recording, name )
        description = name + '.json'
        record = { 
            'filename': name, 
            'transcription': transcription, 
            'timestamp': time.time(),
            'private': private,
        }
        twrite( description, record )
        return record
    def remove_training_data( self, record ):
        name = os.path.basename( record['filename'] )
        name = os.path.join( self.recording_directory, name )
        for n in (name+'.json', name ):
            try:
                os.remove( n )
            except (IOError,OSError) as err:
                pass
    def training_records( self, private=True ):
        for json_file in glob.glob( 
            os.path.join( self.recording_directory, '*.json' )
        ):
            try:
                record = json.loads( open( json_file ).read())
                if os.path.exists( record['filename'] ) and os.stat( record['filename'] ).st_size:
                    if private or not record['private']:
                        yield record 
                else:
                    log.error( 'Training record in %s does not have accompanying data', json_file )
                    os.rename( json_file, json_file+'.stale' )
            except Exception as err:
                pass 
    def transcription_filename( self, transcription ):
        """This isn't "safe" in the universal sense, but it's safe enough for now"""
        if not os.path.exists( self.recording_directory ):
            os.makedirs( self.recording_directory )
        prefix = '_'.join([
            fragment for fragment in 
            ''.join([ c if c.isalnum() else '_' for c in transcription ]).split(
                '_'
            )
            if fragment 
        ]) + '-'
        handle,filename = tempfile.mkstemp(
            suffix='.raw',
            prefix=prefix,
            dir=self.recording_directory,
        )
        os.close( handle )
        return filename

def install_lm_tools( ):
    logging.basicConfig( level = logging.INFO )
    context = Context('default')
    context.ensure_lm_tools()
