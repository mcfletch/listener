from unittest import TestCase
import os
from listener import interpreter
HERE = os.path.dirname( __file__ )

class InterpreterTests( TestCase ):
    def setUp( self ):
        self.interpreter = interpreter.Interpreter()
    def tearDown( self ):
        pass
    def test_punctuation(self):
        for text, expected in [
            (',comma', ','), 
            ('/slash this and that',  '/this and that'), 
            ('class director (open-paren object )close-paren :colon', 'class director (object):'), 
            ('def blue _under there (left-paren', 'def blue_there ('), 
            ('three .point five', '3.5'), 
            ('{open-brace five :colon "double-quote that', '{5:"that'), 
            ('}close-brace [open-bracket 5 ]close-bracket', '}[5]'), 
            ('(open-paren (open-paren',  '(('), 
            (')close-paren )close-paren',  '))'), 
            ('(open-paren )close-paren',  '()'), 
        ]:
            result = self.interpreter.process(text)
            assert result == expected,  (result, expected, text)
        
