from unittest import TestCase
import tempfile, shutil, os, time
from listener import tokenizer, context

HERE = os.path.dirname(__file__)


class TokenizerTests(TestCase):
    def setUp(self):
        self.workdir = tempfile.mkdtemp(
            prefix='listener-', suffix='-test', dir='/dev/shm'
        )
        self.context = context.Context('default')
        self.tokenizer = tokenizer.Tokenizer(self.context.dictionary_cache)

    def tearDown(self):
        shutil.rmtree(self.workdir, True)  # ignore errors

    def test_tokenizer_categories(self):
        for source, expected in [
            ('ThisIsThat', ['T', 'his', 'I', 's', 'T', 'hat']),
            ('this 23skeedoo', [u'this', u' ', u'23', u'skeedoo']),
            ('Just so.', [u'J', u'ust', u' ', u'so', u'.']),
            ('x != this', [u'x', u' ', u'!=', u' ', u'this']),
            ('x == this', [u'x', u' ', u'==', u' ', u'this']),
            (
                'http://test.this.that/there?hello&ex#anchor',
                [
                    u'http',
                    u'://',
                    u'test',
                    u'.',
                    u'this',
                    u'.',
                    u'that',
                    u'/',
                    u'there',
                    u'?',
                    u'hello',
                    u'&',
                    u'ex',
                    u'#',
                    u'anchor',
                ],
            ),
            ('# What he said', [u'#', u' ', u'W', u'hat', u' ', u'he', u' ', u'said']),
        ]:
            raw_result = list(self.tokenizer.runs_of_categories(source))
            result = [x[1] for x in raw_result]
            assert result == expected, (source, result, raw_result)

    def test_tokenizer_tokens(self):
        for source, expected in [
            ('ThisIsThat', [['T', 'his', 'I', 's', 'T', 'hat']]),
            ('This is that', [[u'T', u'his'], [u' '], [u'is'], [u' '], [u'that']]),
            ('x != this', [[u'x'], [u' '], [u'!='], [u' '], [u'this']]),
            ('0x3faD', [['0', 'x', '3', 'fa', 'D']]),
            # TODO: this test-case is a bit arbitrary, the result is basically
            # 'some set of randomly divided values'
            (
                '!@#$%^&*()_+-=[]{}\\|:;\'",.<>/?',
                [[u'!@#$%^&*()'], [u'_'], [u'+-=[]{}\\|:;\'"'], [u',.'], [u'<>/?']],
            ),
            (
                'elif moo:\n\tthat()',
                [[u'elif'], [u' '], [u'moo'], [u':'], [u'\n\t'], [u'that'], [u'()']],
            ),
        ]:
            raw_result = list(
                self.tokenizer.runs_of_tokens(self.tokenizer.runs_of_categories(source))
            )
            result = [[x[1] for x in result] for result in raw_result]
            assert result == expected, (source, result, raw_result)

    def test_expand(self):
        for source, expected in [
            # ('0x23ad',['zero','x','two','three','ad']), # word "Ad" as in advertisement
            ('!==', ['!=not-equal', '=equals']),
            ('"', ['"double-quote']),
            ('ThisIsThat', ['cap', 'camel', u'this', u'is', u'that']),
            ('23skido', ['two', 'three', 'no-space', u'skid', u'o', 'spaces']),
        ]:
            raw_result = list(
                self.tokenizer.runs_of_tokens(self.tokenizer.runs_of_categories(source))
            )
            expanded = list(self.tokenizer.expand(raw_result))[0]
            assert expanded == expected, (source, expanded)

    def test_break_down_name(self):
        for input, expected in [
            ('thisTest', ['camel', 'this', 'test']),
            ('ThisTest', ['cap', 'camel', 'this', 'test']),
            ('that_test', ['that', '_under-score', 'test']),
            # ('oneshot',['no-space','one','shot','spaces']), # would need statistical model
        ]:
            result = self.tokenizer.parse_camel(input)
            assert result == expected, (input, result)

    def test_run_together(self):
        dictionary = self.context.dictionary_cache
        dictionary.add_dictionary_iterable(
            [('kde', 'K D IY'), ('veridian', 'MOO'),]
        )
        for run_together, expected in [
            ('om', ['o', 'm']),
            ('buildthis', ['build', 'this']),
            ('Moveoverage', ['move', 'over', 'age']),
            ('generateov', ['generate', 'o', 'v']),
            ('qapplication', ['q', 'application']),
            ('kdebuildingwindow', ['kde', 'building', 'window']),
            ('VeridianEgg', ['veridian', 'egg']),
            ('Veridian', ['veridian']),
            # ('oneshot',['one','shot']), # would need statistical model
        ]:
            result = self.tokenizer.parse_run_together(run_together)
            assert result == expected, (run_together, result)

    def test_tokenizer_accept(self):
        dictionary = self.context.dictionary_cache
        dictionary.add_dictionary_iterable(
            [('kde', 'K D IY'), ('veridian', 'MOO'),]
        )
        expected = [
            ('test[this]', [['test', '[open-bracket', 'this', ']close-bracket',]]),
            (
                'this.test(this,that)',
                [
                    [
                        'this',
                        '.dot',
                        'test',
                        '(open-paren',
                        'this',
                        ',comma',
                        'that',
                        ')close-paren',
                    ]
                ],
            ),
            (
                'class Veridian(object):',
                [
                    [
                        'class',
                        ' ',
                        'cap',
                        'veridian',
                        '(open-paren',
                        'object',
                        ')close-paren',
                        ':colon',
                    ]
                ],
            ),
            (
                'objectReference.attributeReference = 34 * deltaValue',
                [
                    [
                        'camel',
                        'object',
                        'reference',
                        '.dot',
                        'camel',
                        'attribute',
                        'reference',
                        ' ',
                        '=equals',
                        ' ',
                        'three',
                        'four',
                        ' ',
                        '*asterisk',
                        ' ',
                        'camel',
                        'delta',
                        'value',
                    ]
                ],
            ),
            (
                'GLUT_SOMETHING_HERE = 0x234A',
                [
                    [
                        'all',
                        'caps',
                        'glut',
                        '_under-score',
                        'all',
                        'caps',
                        'something',
                        '_under-score',
                        'all',
                        'caps',
                        'here',
                        ' ',
                        '=equals',
                        ' ',
                        'zero',
                        'x',
                        'two',
                        'three',
                        'four',
                        'cap',
                        'a',
                    ]
                ],
            ),
            (
                'class VeridianEgg:',
                [['class', ' ', 'cap', 'camel', 'veridian', 'egg', ':colon']],
            ),
            ('newItem34', [['camel', 'new', 'item', 'three', 'four']],),
            (
                'new_item_34',
                [['new', '_under-score', 'item', '_under-score', 'three', 'four']],
            ),
            ('"""this"""', [['"""triple-quote', 'this', '"""triple-quote']],),
            (
                "'''this'''",
                [["'''triple-single-quote", 'this', "'''triple-single-quote"]],
            ),
            (
                "testruntogether=2",
                [["no-space", "test", "run", "together", 'spaces', '=equals', 'two']],
            ),
            (
                "addressof( 2 )",
                [
                    [
                        'no-space',
                        'address',
                        'of',
                        'spaces',
                        '(open-paren',
                        ' ',
                        'two',
                        ' ',
                        ')close-paren',
                    ]
                ],
            ),
            ("1", [["one"]],),
        ]
        for line, expected in expected:
            result = list(self.tokenizer([line]))
            assert result == expected, (line, result)
