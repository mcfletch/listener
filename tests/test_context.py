from unittest import TestCase
import tempfile, shutil, os
from listener import context, codetowords

class ContextTests( TestCase ):
    def setUp( self ):
        self.workdir = tempfile.mkdtemp( 
            prefix='listener-', suffix='-test', dir='/dev/shm' 
        )
        self.context = context.Context(
            'default', directory=os.path.join(self.workdir,'config')
        )
    def tearDown( self ):
        shutil.rmtree( self.workdir, True ) # ignore errors
    
    def test_init( self ):
        pass 
    def test_user_default( self ):
        directory = context.base_config_directory()
        if 'XDG_CONFIG_HOME' in os.environ:
            assert directory.startswith( os.environ['XDG_CONFIG_HOME'] ), directory 
        else:
            assert directory.startswith( os.path.expanduser( '~' )), directory
    def test_language_model_directory( self ):
        assert os.path.exists( self.context.language_model_directory )
    def test_hmm_directory( self ):
        assert os.path.exists( self.context.hmm_directory )
    def test_buffer_directory( self ):
        assert os.path.exists( self.context.buffer_directory )
    def test_language_model_file( self ):
        assert os.path.exists( self.context.language_model_file )
    def test_dictionary_file( self ):
        assert os.path.exists( self.context.dictionary_file )
    
    def test_alsa_devices( self ):
        devices = self.context.available_alsa_devices()
        # obviously these *could* be false, but then you're running on a machine
        # that couldn't run the task...
        assert devices['input'], devices 
        assert devices['output'], devices
    
    def test_transcriptions_noguess( self ):
        context.twrite( self.context.dictionary_file, 'goodbye\tG UH D B AY' )
        known = self.context.transcriptions( [ 'toodles','goodbye' ] )
        assert known['goodbye'], known 
        assert not known['toodles'], known 
    def test_transcriptions_guess( self ):
        context.twrite( self.context.dictionary_file, 'goodbye\tG UH D B AY' )
        known = self.context.transcriptions( [ 'toodles','goodbye' ], guess=True )
        assert known['goodbye'], known 
        assert known['toodles'], known 
    
    def test_create_small_context( self ):
        self.context.add_statements([
            'one',
            'two',
            'three',
            'four',
            'five',
            'six',
            'seven',
            'eight',
            'nine',
            'ten',
            'eleven',
            'twelve',
        ])
        self.context.regenerate_language_model()
    def test_punctuation_added( self ):
        names = codetowords.OP_NAMES.values()
        expanded = []
        for name in names:
            if ' ' in name:
                expanded.extend( name.split( ' '))
            else:
                expanded.append( name )
        mapping = self.context.transcriptions( expanded )
        for name,translated in mapping.items():
            assert translated, name
        
    
class AudioContextTests( TestCase ):
    def setUp( self ):
        self.workdir = tempfile.mkdtemp( prefix='listener-', suffix='-test' )
        self.context = context.Context('default', directory=self.workdir)
        self.audio_context = self.context.audio_context( 'moo' )
    def tearDown( self ):
        shutil.rmtree( self.workdir, True ) # ignore errors
    def test_save_settings( self ):
        self.audio_context.save_settings()
        assert os.path.exists( self.audio_context.settings_file )
    def test_round_trip_settings( self ):
        base = self.audio_context.settings
        base['moo'] = 'this'
        self.audio_context.save_settings()
        assert os.path.exists( self.audio_context.settings_file )
        new_context = context.AudioContext( self.context, 'moo' )
        assert new_context.settings['moo'] == 'this'
    def test_transcription_filename( self ):
        filename = self.audio_context.transcription_filename( '  this/../:is a _+=| test ' )
        assert os.path.exists( filename )
        base = os.path.basename( filename )
        assert base.startswith( 'this_is_a_test-' ), base
        assert os.path.exists( self.audio_context.recording_directory )

    def test_add_training_data( self ):
        sample = os.path.abspath(os.path.join( self.workdir, 'test.raw' ))
        context.twrite( sample, 'Moo' )
        transcription = 'this_is_a_test'
        record = self.audio_context.add_training_data( sample, transcription )
        assert os.path.exists(record['filename']), record 
        assert record['transcription'] == transcription, record 
    
        records = list(self.audio_context.training_records())
        assert records == [ record ], records 
    
        self.audio_context.remove_training_data( record )
        records = list(self.audio_context.training_records())
        assert records == [ ], records 
        

    
