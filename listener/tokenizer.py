import unicodedata,logging,re,os,locale,itertools
from collections import deque
from ._bytes import as_unicode
log = logging.getLogger(__name__)

CODING = re.compile( r'coding[:=]\s*([-\w.]+)' )

def grouper(iterable, n, fillvalue=None):
    "Collect data into fixed-length chunks or blocks"
    args = [iter(iterable)] * n
    return itertools.izip_longest(fillvalue=fillvalue, *args)

class PeekingGenerator(object):
    STOP_ERROR = object()
    def __init__( self, source ):
        self.source = iter(source)
        self.peeked = deque()
    def __iter__( self ):
        return self
    def next( self ):
        """Retrieve our next item"""
        try:
            return self.peeked.popleft()
        except IndexError:
            return self.source.next()
    def peek( self ):
        """Peek at the next item
        
        Will return self.STOP_ERROR if the 
        iterable is exhausted when you call peek()
        """
        try:
            value = self.source.next()
        except StopIteration as err:
            return self.STOP_ERROR
        else:
            self.peeked.append( value )
            return value 


class Tokenizer( object ):
    def __init__( self,dictionary, run_together_guessing=True ):
        self.dictionary = dictionary 
        self.SPECIAL_COMBINERS = self.locale_specials()
        self.category_cache = {}
        self.run_together_guessing = run_together_guessing
    def locale_specials(self):
        if 'LANG' in os.environ:
            locale.setlocale(locale.LC_ALL,os.environ['LANG'])
        env = locale.localeconv()
        return u''.join([as_unicode(env[k]) for k in [
            'decimal_point',
            'thousands_sep',
        ]])
    BASE_TYPE_MAP = {
        # consider category X -> basic category
        'Pd':'P',
        'Pe':'P',
        'Pf':'P',
        'Pi':'P',
        'Po':'P', # but the SPECIAL_COMBINERS are pulled out first...
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
    
    def category_for_char( self, char ):
        """Caches char:category decisions to speed up tokenization"""
        new_category = self.category_cache.get( char )
        if new_category is None:
            raw_category = unicodedata.category(char)
            if char in self.SPECIAL_COMBINERS:
                new_category = 'Px'
            else:
                new_category = self.BASE_TYPE_MAP.get(raw_category,raw_category)
            self.category_cache[char] = new_category
        return new_category
    
    def runs_of_categories( self, text ):
        """Produce iterable of runs-of-unicode-categories"""
        text = as_unicode( text )
        current = None
        category=None
        for char in text:
            new_category = self.category_for_char( char )
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
        runs_of_categories = PeekingGenerator(runs_of_categories)
        for category,chars in runs_of_categories:
            assert isinstance(chars,unicode), (type(chars),chars)
            if category == 'Px':
                # a combiner that is a terminal but only iff the 
                # character after is a splitting character...
                next = runs_of_categories.peek()
                if next is runs_of_categories.STOP_ERROR:
                    # is a real terminal...
                    category = 'P'
                elif next[0] in self.SEPARATES_WORDS:
                    category = 'P'
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
                elif chars in self.PUNCTUATION_NAMES:
                    result.append( self.PUNCTUATION_NAMES[chars] )
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
        '\r\n': 'new-line',
        '\r': 'new-line',
        '\n': 'new-line',
        '!': '!exclamation-point',
        '!=': '!=not-equal',
        '"': '"double-quote',
        '#': '#sharp-sign',
        '$': '$dollar-sign',
        '%': '%percent',
        '&': '&ampersand',
        "'": "'quote",
        "'''":"'''triple-single-quote",
        '"""':'"""triple-quote',
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
        if isinstance( text, (unicode,str)):
            text = [text]
        for statement in text:
            tokens = []
            for expanded in self.expand(statement):
                tokens.extend( expanded )
            yield tokens 
    
    _cached_run_together = None
    def cached_run_together( self, name ):
        if self._cached_run_together is None:
            self._cached_run_together = {}
        return self._cached_run_together.get(name )
    
    def parse_run_together( self, name ):
        """Parse dictionary words that are run together"""
        possible = self.cached_run_together( name )
        if possible:
            return possible[:]
        else:
            self._cached_run_together[name] = possible = self._parse_run_together(
                name 
            )
            return possible
    
    def _parse_run_together( self, name ):
        if (not self.dictionary) or not (self.run_together_guessing):
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
        
    def is_all_caps( self, name ):
        has_letters = False 
        all_uppercase = False 
        for (category,char) in name:
            if category.startswith('L'):
                has_letters = True
                if category != 'Lu':
                    return False 
        return has_letters
        
    def is_cap_camel( self, name ):
        """Go through name checking for camel-case"""
        has_letters = False
        for (category,char) in name:
            if category.startswith('L'):
                has_letters = True 
                if category != 'L':
                    return False 
        return has_letters
    def is_camel( self, name ):
        return len(name) > 1 and name[0][0] == 'Ll' and self.is_cap_camel( name[1:] )
        
    def combine_ls( self, name ):
        """Combine all L-prefixed items..."""
        result = []
        for (category,chars) in name:
            if (
                category == 'Ll' and 
                result and 
                result[-1][0] == 'Lu' 
                and len(result[-1][1]) == 1
            ):
                result[-1] = ('L',result[-1][1]+chars)
            else:
                result.append( (category,chars) )
        return result
    
    def looks_like_camel( self, name ):
        if len(name) > 1:
            first,rest = name[0],name[1:]
            if first[0] == 'Ll':
                return self.looks_like_cap_camel( rest, False )
        return False
    def looks_like_cap_camel( self, name, whole=True ):
        if whole:
            min = 4
        else:
            min = 2
        if len(name) >= min:
            for (upper,lower) in grouper( name, 2 ):
                if not (
                    upper[0] == 'Lu' and 
                    len(upper[1]) == 1 and 
                    lower and 
                    lower[0] == 'Ll'
                ):
                    return False
            return True
        return False
    def looks_like_dunder( self, name ):
        if len(name)>=3 and name[0] == self.DUNDER and name[-1] == self.DUNDER:
            return True 
        return False
    
    def parse_camel( self, name ):
        if isinstance( name, (bytes,unicode)):
            name = list(self.runs_of_categories( name ))
        else:
            name = list( name )
        
        split = self.combine_ls( name )
        # multiple cases in approximate order of importance
        # based on my experience in Python...
        #  * high-level patterns (URLs being the big one, maybe filenames too)
        #  * wrapping patterns __x__
        #  * combining patterns x_y
        #  * embedded numbers/digits
        #  * simple words, with/without Title
        #  * CapCamelCase
        #  * camelCase 
        #  * ALLCAPSlower
        #  * Num.Num
        #  * Num,Num 
        #  * 0xNum
        #  * Num+
        
        all_caps = self.is_all_caps( split )
        cap_camel_case = self.is_cap_camel( split )
        camel_case = self.is_camel( split )
        
        words = [x for x in split if x[0].startswith('L')]
        split_expanded = []
        for item in split:
            if item[0].startswith('N'):
                split_expanded.extend( self.expand_N( [item] ))
            elif item[0].startswith('P'):
                split_expanded.extend( self.expand_P( [item] ))
            else:
                split_expanded.extend( self.parse_run_together_with_markup(item[1]) )
        
        if len(words) == 1:
            word = words[0][1]
            if len(word) == 1:
                if word.isupper():
                    return ['cap',word.lower()]
                else:
                    # TODO: if not in dictionary, expand to 
                    # "unicode <name of character>"
                    return [word.lower()]
            elif word.isupper():
                return ['all','caps'] + split_expanded
            elif word.title() == word:
                return ['cap']+split_expanded
            else:
                return split_expanded
        else:
            if all_caps:
                return ['all', 'caps'] + split_expanded
            elif cap_camel_case:
                return ['cap','camel'] + split_expanded
            elif camel_case and len(split) > 1:
                return ['camel'] + split_expanded
            else:
                return split_expanded

