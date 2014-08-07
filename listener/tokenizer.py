import unicodedata,logging,re
from ._bytes import as_unicode
log = logging.getLogger(__name__)


CODING = re.compile( r'coding[:=]\s*([-\w.]+)' )

class Tokenizer( object ):
    def __init__( self,dictionary ):
        self.dictionary = dictionary 
    BASE_TYPE_MAP = {
        # consider category X -> basic category
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
        'P','Z','Zs','Po','Sc','Ps','Pe','Sm','Pd',
        'Cc','C','Cf',
    ])
    def runs_of_tokens( self, runs_of_categories ):
        """Split runs of categories into individual tokens"""
        current_token = []
        for (category,chars) in runs_of_categories:
            assert isinstance(chars,unicode), (type(chars),chars)
            if category in self.SEPARATES_WORDS:
                if current_token:
                    yield current_token
                yield [(category,chars)]
                current_token = []
            else:
                current_token.append( (category,chars) )
        if current_token:
            yield current_token
    
    def expand( self, runs_of_tokens ):
        """Dispatch to our processing functions to expand each token"""
        if isinstance( runs_of_tokens, (bytes,unicode)):
            runs_of_tokens = self.runs_of_tokens(
                self.runs_of_categories( runs_of_tokens )
            )
        # expand any embedded numbers first...
        for token in runs_of_tokens:
            assert isinstance( token, list ), token
            assert len(token),token
            assert len(token[0]) == 2,token
            yield self.expand_token( token )
    DUNDER = ('Pc','__')
    def expand_token( self, token ):
        result = []
        current = []
        def add_current():
            if current:
                result.extend(self.parse_camel( current ))
        # special cases...
        try:
            for (category,chars) in token:
                if category == 'N':
                    add_current()
                    current = []
                    result.extend( self.expand_N( [(category,chars)]))
                elif category == 'Pc':
                    add_current()
                    current = []
                    result.extend( self.expand_P( [(category,chars)]))
                elif category.startswith('P'):
                    add_current()
                    current = []
                    result.extend( self.expand_P( [(category,chars)]))
                else:
                    current.append( (category, chars) )
        except (ValueError,TypeError) as err:
            err.args += (token,)
            raise
        add_current()
        return result 
    
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
    def expand_P( self, token ):
        combined = u''.join([x[1] for x in token])
        fragments = [m.group(0) for m in self.PUNCT_ITER.finditer( combined )]
        result = []
        for fragment in fragments:
            explicit = self.PUNCTUATION_NAMES.get(fragment)
            if not explicit:
                explicit = fragment+unicodedata.name(
                    fragment
                ).replace(u' ',u'-').lower()
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
        "'''":"'''triple-quote",
        '"""':'"""triple-double-quote',
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
        '__': '__dunder',
        '`': '`back-tick',
        '{': '{open-brace',
        '|': '|bar',
        '}': '}close-brace',
        '~': '~tilde',
    }
    LONG_PUNCT = sorted(
        PUNCTUATION_NAMES.keys(),
        key = lambda x: (len(x),x),
        reverse=True,
    )
    PUNCT_ITER = re.compile( u'%s|.'%(
        u'|'.join([
            u'(%s)'%( 
                re.escape(punct)
            )
            for punct in LONG_PUNCT
        ])
    ), re.U|re.M|re.I)

    def __call__( self, text ):
        """Iterate producing all expanded tokens for a given text"""
        for statement in text:
            tokens = []
            for expanded in self.expand(statement):
                tokens.extend( expanded )
            yield tokens 
        
    def parse_run_together( self, name ):
        """Parse dictionary words that are run together"""
        if not self.dictionary:
            return [name]
        # split up the name looking for runtogether words...
        name = name.lower()
        if name in self.dictionary:
            return [name]
        # TODO: use statistics to decide which sub-words are the most 
        # *likely* to occur, rather than always searching for a longer match...
        
        # anything smaller than 1 is *always* in the dictionary...
        prefixes = [name[:i] for i in range(1,len(name))]
        mapped = self.dictionary.have_words( *prefixes )
        possibles = []
        for (prefix,translations) in sorted(mapped.items(),key=lambda x: len(x[0]),reverse=True):
            if translations:
                suffix = name[len(prefix):]
                if suffix in self.dictionary:
                    return [prefix,suffix]
                remaining = self.parse_run_together( suffix )
                if len(prefix) > 1 and remaining != [suffix]:
                    return [prefix]+remaining
                possibles.append( [ prefix ] + remaining )
        suffixes = [name[-i:] for i in range(1,len(name))]
        mapped = self.dictionary.have_words( *suffixes )
        possibles = []
        for (suffix,translations) in sorted(mapped.items(),key=lambda x: len(x[0]),reverse=True):
            if translations:
                prefix = name[:-len(suffix)]
                if prefix in self.dictionary:
                    return [prefix,suffix]
                remaining = self.parse_run_together( prefix )
                if len(suffix) > 1 and remaining != [prefix]:
                    return remaining+[suffix]
                possibles.append( remaining+[suffix] )
        if len(name) < 3:
            return [c for c in name]
        return [name]

    def parse_run_together_with_markup( self, name ):
        base = self.parse_run_together( name )
        if len(base) > 1:
            return ['no-space']+base+['spaces']
        return base
        
    def is_title( self, first, second ):
        return first[0] == 'Lu' and len(first) == 1 and second[0] == "Ll"
    def is_all_caps( self, name ):
        return all([item[0]=='Lu' for item in name])
    def is_camel( self, name ):
        """Go through name checking for camel-case"""
        while len(name)>1:
            if not self.is_title( name[0], name[1] ):
                return False 
            name = name[2:]
        return not name # no trailing bits...

    def parse_camel( self, name ):
        if isinstance( name, (bytes,unicode)):
            name = list(self.runs_of_categories( name ))
        
        all_caps = self.is_all_caps( name )
        cap_camel_case = self.is_camel( name )
        camel_case = len(name) > 1 and self.is_camel(name[1:])
        
        
        words = [x for x in split if not x.isdigit()]
        split_expanded = []
        for item in split:
            if item.isdigit():
                split_expanded.extend( [digit(x) for x in item])
            else:
                split_expanded.append( item )

        run_together_expansion = sum([
            self.parse_run_together_with_markup(x) 
            for x in split_expanded
        ],[])
        result = run_together_expansion
        if len(words) == 0:
            # e.g. numeric fragment of a name...
            pass
        elif len(words) == 1:
            if words[0].isupper():
                result = ['all','caps'] + run_together_expansion
            elif words[0].title() == words[0]:
                result = ['cap']+run_together_expansion
        else:
            if all_caps:
                result = ['all', 'caps'] + run_together_expansion
            elif cap_camel_case:
                result = ['cap','camel'] + run_together_expansion
            elif camel_case and len(split) > 1:
                result = ['camel'] + run_together_expansion
        return result

