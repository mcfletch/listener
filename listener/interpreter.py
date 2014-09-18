import os,re
HERE = os.path.dirname( __file__ )
TYPING = os.path.join( HERE, 'typing.csv' )
class Interpreter( object ):
    """Sketch of an interpreter for dictation -> typing
    
    We still need:
    
        * interpretation-as-command (call a function)
        * sub-interpreters (e.g. number interpreter)
        * state-change pattern (e.g. no-space, cap, title)
    """
    def __init__( self ):
        self.matchers = []
        self.load()
    def load( self ):
        for line in open(TYPING).read().splitlines():
            try:
                pattern,text = line.split('\t')
            except Exception:
                # skip null lines...
                continue
            matcher = re.compile( pattern, re.I|re.U|re.DOTALL )
            self.matchers.append( (matcher, self.action(text)))
    def action(self,  text):
        if text.startswith( ':') and not text.startswith( '::'):
            return self.lookup_function( text[1:])
        elif text.startswith( ':'):
            return text[1:]
        else:
            return text
    def process( self, text ):
        for matcher,replacement in self.matchers:
            text= matcher.sub( replacement , text )
        return text
    def lookup_function(self, specifier):
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

def caps( match ):
    return match.group(1).title()
def all_caps( match ):
    return match.group(1).upper()
def lowercase( match ):
    return match.group(1).lower()
def cap_next(match):
    this, next = match.group('this'), match.group('next')
    if next:
        return u'%s %s'%(this, next.title())
    else:
        return this
