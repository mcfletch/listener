from unittest import TestCase
import tempfile, shutil, os, time
from listener import codetowords
HERE = os.path.dirname( __file__ )

class CodetoWordsTests( TestCase ):
    def setUp( self ):
        self.workdir = tempfile.mkdtemp( 
            prefix='listener-', suffix='-test', dir='/dev/shm' 
        )
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
                [['camel', 'object', 'Reference', '.dot', 'camel', 'attribute', 'Reference', '=equals', 'number', 'three','four', 'end number', '*asterisk', 'camel', 'delta', 'Value']],
            ),
            (
                'GLUT_SOMETHING_HERE = 0x234',
                [['all', 'caps', 'GLUT', 'under', 'all', 'caps', 'SOMETHING', 'under', 'all', 'caps', 'HERE', '=equals', 'number', 'zero', 'x', 'two', 'three', 'four', 'end number']],
            ),
            (
                'class VeridianEgg:',
                [['class', 'cap', 'camel', 'Veridian', 'Egg', ':colon']],
            ),
            (
                'newItem34',
                [['camel','new','Item','three','four']],
            ),
            (
                'new_item_34',
                [['new','under','item','under','three','four']],
            ),
            (
                '"""this"""',
                [[
                    '"""triple-quote',
                    #'this',
                    '"""triple-quote'
                ]],
            ),
            (
                "'''this'''",
                [[
                    "'''triple-single-quote",
                    #'this',
                    "'''triple-single-quote"
                ]],
            ),
        ]
        for line,expected in expected:
            result = codetowords.codetowords([line])
            assert result == expected, (line, result)
