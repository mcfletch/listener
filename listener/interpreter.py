import os,re,  logging
log = logging.getLogger(__name__)
HERE = os.path.dirname( __file__ )
TYPING = os.path.join( HERE, 'typing.csv' )

class Interpreter( object ):
    """Sketch of an interpreter for dictation -> typing
    
    Currently missing is the ability to do meta-commands:
    
        * trigger a GUI operation
        * generate a new utterance (e.g. splitting utterances)
        
            * 'switch to console c d ~tilde' -> two commands to two different processes,
              the context for processing commands needs to change mid-way through the 
              processing operation...
            
            * ':colon new line dedent' -> three commands to 1 process...
    """
    def __init__( self ):
        self.matchers = []
        self.load()
    def load( self ):
        """Load a flat-file definition of an interpretation context"""
        for line in open(TYPING).read().splitlines():
            try:
                pattern,text = line.split('\t')
            except Exception:
                # skip null lines...
                if line.strip():
                    log.error( 'Unable to read line %r, ignoring',  line)
                continue
            matcher = re.compile( pattern, re.I|re.U|re.DOTALL )
            self.matchers.append( (matcher, self.action(text)))
    def action(self,  text):
        """Determine what to do given the replacement text from a flat-file import"""
        if text.startswith( ':') and not text.startswith( '::'):
            return self.lookup_function( text[1:])
        elif text.startswith( ':'):
            return text[1:]
        else:
            return text
    def lookup_function(self, specifier):
        """Lookup a function based on a specifier in a flat-file import"""
        split = specifier.split('.')
        if not split > 1:
            raise ValueError('%r is not a valid function specifier')
        try:
            source = __import__('.'.join(split[:-1]), {}, {}, '.'.join(split))
        except ImportError:
            raise ValueError('%r could not be imported'%(specifier))
        try:
            return getattr( source,  split[-1])
        except AttributeError:
            raise ValueError( '%r was not defined in %s'%(split[-1], source))
    def __call__( self, record ):
        text = record.get('text')
        for matcher,replacement in self.matchers:
            text= matcher.sub( replacement , text )
        record['interpreted'] = text
        # eventually we'll return N records...
        return [ record ]

def caps( match ):
    return match.group(1).title()
def all_caps( match ):
    next = match.group('next')
    return next.upper()
def lowercase( match ):
    return match.group(1).lower()
def cap_next(match):
    this, next = match.group('this'), match.group('next')
    if next:
        return u'%s %s'%(this, next.title())
    else:
        return this
def cap_camel(match):
    next = match.group('next')
    return "".join([s.title() for s in next.split(' ')])
def camel(match):
    next = match.group('next')
    fragments = next.split()
    return u'%s%s'%(fragments[0],"".join([s.title() for s in fragments[1:]]))

def collapse_spaces( match ):
    base = match.group(0)
    return base.replace(' ', '')
    
def new_line(match): return '\n'
def tab_key(match): return '\t'
def backspace(match): return '\b'
def dunder_wrap(match): 
    next = match.group('next')
    return '__%s__'%(next)
    
