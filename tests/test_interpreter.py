from unittest import TestCase
import os
from listener import interpreter

HERE = os.path.dirname(__file__)


class InterpreterTests(TestCase):
    def setUp(self):
        self.interpreter = interpreter.Interpreter()

    def tearDown(self):
        pass

    def test_punctuation(self):
        for text, expected in [
            (',comma', ','),
            ('/slash this and that', '/this and that'),
            (
                'class director (open-paren object )close-paren :colon',
                'class director(object):',
            ),
            ('def blue _under there (left-paren', 'def blue_there('),
            ('three .point five', '3.5'),
            ('{open-brace five :colon "double-quote that', '{5:"that'),
            ('}close-brace [open-bracket 5 ]close-bracket', '}[5]'),
            ('(open-paren (open-paren', '(('),
            (')close-paren )close-paren', '))'),
            ('(open-paren )close-paren', '()'),
            (
                'cap he opened the door .period then he walked away .period good',
                'He opened the door. Then he walked away. Good',
            ),
            ('identifier no-space 2 _under-score 3', 'identifier2_3'),
            ('id _under three _under four', 'id_3_4'),
            ('two .point three four five', '2.345'),
            ('two *asterisk right _under margin', '2*right_margin'),
            ('all caps this _under that', 'THIS_THAT'),
            ('camel this and that', 'thisAndThat'),
            ('cap camel this and that', 'ThisAndThat'),
            ('test -hyphen moo', 'test-moo'),
            ('@at property', '@property'),
            (
                'object .dot method _under name (open-paren __dunder cap this __dunder )close-paren',
                'object.method_name (__This__)',
            ),
            ('new line', '\n'),
            ('full stop', '.'),
            ('tab-key', '\t'),
            ('back space', '\b'),
            (
                '(open-paren "quote this and that "quote )close-paren',
                '("this and that")',
            ),
            ('__dunder this _under those __dunder', '__this_those__',),
            ('__dunder init __dunder', '__init__',),
            ('the three medals', 'the 3 medals',),
            ('spell out three', 'three'),
            ('spell out __dunder', '__dunder'),
            ('correct that', interpreter.Command('correct-that'),),
            (
                'verbatim three four five verbatim off',
                interpreter.Command('verbatim-content', content='three four five'),
            ),
            (
                'verbatim three four five',
                interpreter.Command('verbatim-content', content='three four five'),
            ),
            # Macro functionality is not yet that important
            #            (
            #                'pie main line',
            #                'if __name__ == "__main__":\n\t'
            #            ),
        ]:
            record = list(self.interpreter({'text': text}))[0]
            assert record['interpreted'] == expected, (
                record['interpreted'],
                expected,
                text,
            )

    def test_lookup(self):
        assert (
            self.interpreter.lookup_function('listener.interpreter.caps')
            is interpreter.caps
        )
