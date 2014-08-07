import unicodedata
from ._bytes import as_unicode

PUNCTUATION_NAMES = {
    # TODO: allow user overrides for all of these
    # so they can use star-star or left-paren or some custom 
    # word if they want...
    '\n': 'new-line',
    '!': '!exclamation-point',
    '!=': '!=not-equal',
    '"': '"double-quote',
    '#': '#sharp-sign',
    '$': '$dollar-sign',
    '%': '%percent',
    '&': '&ampersand',
    "'": "'quote",
    '(': '(open-paren',
    ')': ')close-paren',
    '*': '*asterisk',
    '**': '**asterisk-asterisk',
    '+': '+plus',
    ',': ',comma',
    '-': '-hyphen',
    '.': '.dot',
    '...': '...ellipsis',
    '/': '/slash',
    ':': ':colon',
    '://': ':colon /slash /slash',
    ';': ';semi-colon',
    '<': '<less-than',
    '=': '=equals',
    '==': '==equal-equal',
    '>': '>greater-than',
    '?': '?question-mark',
    '@': '@at',
    '[': '[open-bracket',
    '\\': '\\back-slash',
    ']': ']close-bracket',
    '^': '^caret',
    '_': '_under-score',
    '`': '`back-tick',
    '{': '{open-brace',
    '|': '|bar',
    '}': '}close-brace',
    '~': '~tilde',
}

class Tokenizer( object ):
    def __init__( self,dictionary ):
        self.dictionary = dictionary 
    BASE_TYPE_MAP = {
        # consider category X -> basic category
        'Pc':'P',
        'Pd':'P',
        'Pe':'P',
        'Pf':'P',
        'Pi':'P',
        'Po':'P',
        'Ps':'P',
        
        'S': 'P',
        'Sm':'P',
        'Sc':'P',
        'Sk':'P',
        'So':'P',
        
        'Nd':'N',
        'No':'N',
        'Nl':'N',
        
        'Zl':'Z',
        'Zs':'Z',
        'Zp':'Z',
    }
    def runs_of_categories( self, text ):
        """Produce iterable of runs-of-unicode-categories"""
        text = as_unicode( text )
        current = None
        category=None
        for char in text:
            raw_category = unicodedata.category(char)
            new_category = self.BASE_TYPE_MAP.get(raw_category,raw_category)
            if new_category != category:
                if current:
                    yield category,current 
                current = char
                category = new_category
            else:
                if current:
                    current = current + char 
                else:
                    current = char
        if current:
            yield category,current
    SEPARATES_WORDS = set([
        'P','Z','Zs','Po','Sc','Ps','Pe','Pc','Sm','Pd',
        'Cc','C','Cf',
    ])
    def runs_of_tokens( self, runs_of_categories ):
        """Split runs of categories into individual tokens"""
        current_token = []
        for (category,chars) in runs_of_categories:
            if category in self.SEPARATES_WORDS:
                if current_token:
                    yield current_token
                yield [(category,chars)]
                current_token = []
            else:
                current_token.append( (category,chars) )
        if current_token:
            yield current_token
    
    def expand_N( self, token ):
        """Expand an N-token into words"""
        # TODO: currently is hopelessly *not* unicode functional
        combined = u''.join([x[1] for x in token])
        result = []
        for char in combined:
            explicit = self.DIGITS.get(char)
            if not explicit:
                explicit = unicodedata.name(char).replace(u' ',u'-').lower()
            result.append( explicit )
        return result
    DIGITS = {
        '0':'zero',
        '1':'one',
        '2':'two',
        '3':'three',
        '4':'four',
        '5':'five',
        '6':'six',
        '7':'seven',
        '8':'eight',
        '9':'nine',
        'a':'a',
        'A':'cap a',
        'b':'b',
        'c':'c',
        'C':'cap c',
        'd':'d',
        'D':'cap D',
        'e':'e',
        'E':'cap E',
        'f':'f',
        'F':'cap F',
        'x':'x',
        'X':'x',
        '-':'minus',
        '+':'plus',
        '.':'.dot',
    }
        

def test_tokenizer_categories( ):
    tok = Tokenizer(None)
    for source,expected in [
        ('ThisIsThat',['T','his','I','s','T','hat']),
        ('this 23skeedoo',[u'this', u' ', u'23', u'skeedoo']),
        ('Just so.',[u'J', u'ust', u' ', u'so', u'.']),
        ('x != this',[u'x', u' ', u'!=', u' ', u'this']),
        ('x == this',[u'x', u' ', u'==', u' ', u'this']),
        (
            'http://test.this.that/there?hello&ex#anchor',
            [
                u'http', u'://', u'test', u'.', u'this', u'.', u'that', 
                u'/', u'there', u'?', u'hello', u'&', u'ex', u'#', u'anchor'
            ]
        ),
        ('# What he said',[u'#', u' ', u'W', u'hat', u' ', u'he', u' ', u'said']),
    ]:
        raw_result = list(tok.runs_of_categories(source))
        result = [x[1] for x in raw_result]
        assert result == expected, (source,result,raw_result)

def test_tokenizer_tokens( ):
    tok = Tokenizer(None)
    for source,expected in [
        ('ThisIsThat',[['T','his','I','s','T','hat']]),
        ('This is that',[[u'T', u'his'], [u' '], [u'is'], [u' '], [u'that']]),
        ('x != this',[[u'x'], [u' '], [u'!='], [u' '], [u'this']]),
        ('0x3faD',[['0','x','3','fa','D']]),
        ('!@#$%^&*()_+-=[]{}\\|:;\'",.<>/?',[[u'!@#$%^&*()_+-=[]{}\\|:;\'",.<>/?']]),
        ('elif moo:\n\tthat()',[[u'elif'], [u' '], [u'moo'], [u':'], [u'\n\t'], [u'that'], [u'()']]),
    ]:
        raw_result = list(tok.runs_of_tokens( tok.runs_of_categories(source)))
        result = [[x[1] for x in result] for result in raw_result]
        assert result == expected, (source,result,raw_result)

def test_expand_N( ):
    tok = Tokenizer(None)
    for source,expected in [
        ('0x23ad',['zero','x','two','three','a','d']),
    ]:
        raw_result = list(tok.runs_of_tokens( tok.runs_of_categories(source)))
        expanded = tok.expand_N( raw_result[0] )
        assert expanded == expected, (source,expanded)
