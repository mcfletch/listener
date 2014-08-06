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
    def test_names(self):
        for input,expected in [
            ('thisTest',['camel', 'this', 'Test']),
            ('ThisTest',['cap','camel', 'This', 'Test']),
            ('that_test',['that','under','test']),
        ]:
            result = codetowords.break_down_name( input )
            assert result == expected, (input,result)

    def test_tokens(self):
        dictionary = self.context.dictionary_cache
        dictionary.add_dictionary_iterable([
            ('veridian','MOO'),
            ('glut','MOO'),
        ])
        expected = [
            (
                'test[this]',
                [['test','[open-bracket','this',']close-bracket',]]
            ),
            (
                'this.test(this,that)',
                [['this','.dot','test','(open-paren','this',',comma','that',')close-paren']],
            ),
            
            (
                'class Veridian(object):',
                [['class', 'cap', 'Veridian', '(open-paren', 'object', ')close-paren', ':colon']],
            ),
            (
                'objectReference.attributeReference = 34 * deltaValue',
                [['camel', 'object', 'Reference', '.dot', 'camel', 'attribute', 'Reference', '=equals', 'three','four', '*asterisk', 'camel', 'delta', 'Value']],
            ),
            (
                'GLUT_SOMETHING_HERE = 0x234A',
                [['all', 'caps', 'glut', 'under', 'all', 'caps', 'something', 'under', 'all', 'caps', 'here', '=equals', 'zero', 'x', 'two', 'three', 'four', 'cap a',]],
            ),
            (
                'class VeridianEgg:',
                [['class', 'cap', 'camel', 'veridian', 'egg', ':colon']],
            ),
            (
                'newItem34',
                [['camel','new','item','three','four']],
            ),
            (
                'new_item_34',
                [['new','under','item','under','three','four']],
            ),
            (
                '"""this"""',
                [[
                    '"""triple-quote',
                    'this',
                    '"""triple-quote'
                ]],
            ),
            (
                "'''this'''",
                [[
                    "'''triple-single-quote",
                    'this',
                    "'''triple-single-quote"
                ]],
            ),
            (
                "testruntogether=2",
                [[
                    "no-space", "test", "run", "together", '=equals', 'two'
                ]],
            ),
        ]
        for line,expected in expected:
            result = codetowords.codetowords([line], dictionary=dictionary)
            assert result == expected, (line, result)
    
    def test_run_together( self ):
        dictionary = self.context.dictionary_cache
        dictionary.add_dictionary_iterable([
            ('kde','K D IY'),
            ('veridian','MOO'),
        ])
        for run_together, expected in [
            ('om',['o','m']),
            ('buildthis',['build','this']),
            ('Moveoverage',['move','over','age']),
            ('generateov',['generate','o','v']),
            ('qapplication',['q','application']),
            ('kdebuildingwindow',['kde','building','window']),
            ('VeridianEgg',['veridian','egg']),
            ('Veridian',['veridian']),
        ]:
            result = codetowords.parse_run_together( run_together, dictionary )
            assert result== expected, (run_together,result)
        
