import os,re,  logging
log = logging.getLogger(__name__)
HERE = os.path.dirname( __file__ )
TYPING = os.path.join( HERE, 'typing.csv' )
COMMANDS = os.path.join( HERE, 'metaactions.csv')

class Interpreter( object ):
    """Sketch of an interpreter for dictation -> typing
    
    Currently missing is the ability to do meta-commands:
    
        * trigger a Listener GUI operation
        
        * trigger a GUI operation in the client application
        
        * trigger a change to a new interpretation context
        
            * needs to be an API for the client app to do this too, so that 
              e.g. we can use Eric's "editor.inDocstring()" and the like to 
              select sub-contexts intelligently
        
        * ability to choose "initial space" or not
        
        * generate a new utterance (e.g. splitting utterances)
        
            * 'switch to console c d ~tilde' -> two commands to two different processes,
              the context for processing commands needs to change mid-way through the 
              processing operation...
        
    """
    def __init__( self ):
        self.matchers = []
        self.commands = []
        self.load()
        self.context = ['listener']
    def load( self ):
        """Load a flat-file definition of an interpretation context"""
        for line in open(COMMANDS).read().splitlines():
            context, command, tag = [x.decode('utf-8') for x in line.split('\t')]
            if not tag:
                tag = '-'.join(command.split())
            if not context:
                context = '.*'
            matcher = re.compile(u'\\b%s\\b'%(command,),  re.U|re.I|re.DOTALL)
            self.commands.append((context, matcher, tag))
        for line in open(TYPING).read().splitlines():
            try:
                pattern,text = [x.decode('utf-8') for x in line.split('\t')]
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
    def find_command(self,  text,  command_record):
        """Iteratively split up text by any instances of command..."""
        context, matcher, tag = command_record
        match = matcher.search(text)
        index = 0
        while match:
            before = text[index:match.start()]
            if before:
                yield before 
            yield Command(tag, **match.groupdict())
            index = match.end()
            match = matcher.search(text, index)
        rest = text[index:]
        if rest:
            yield rest
    def __call__( self, record ):
        text = record.get('text')
        
        sub_records = [text]
        for command_record in self.commands:
            # IFF command_record[0] matches current_context
            expanded = []
            for item in sub_records:
                if isinstance(item, Command):
                    expanded.append( item )
                else:
                    expanded.extend( self.find_command(item, command_record))
            sub_records = expanded
        expanded = []
        for item in sub_records:
            local_record = record.copy()
            if isinstance( item, (bytes, unicode)):
                for matcher,replacement in self.matchers:
                    item= matcher.sub( replacement, item )
            expanded.append( item )
            local_record['interpreted'] = item
            yield local_record

def caps( match ):
    return match.group(1).title()
def all_caps( match ):
    next = match.group('next')
    return next.upper()
def lowercase( match ):
    return match.group(1).lower()
def full_stop(match):
    this, next = match.group('this'), match.group('next')
    if this is None:
        this = '.'
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
    
def spell_out_escape(match):
    word = match.group('word')
    return u'\u8eb2%s\u8eb2'%(word)
def spell_out_unescape(match):
    return match.group('word')

class Command(object):
    """Control flow jump on detection of a (meta) command"""
    def __init__(self,  command,  *args,  **named):
        self.command = command 
        self.args = args
        self.named = named
    def __eq__(self,  other):
        return (
            other.command == self.command and 
            other.args == self.args and 
            other.named == self.named
        )
    def __unicode__(self):
        return u'%s -> %s'%(
            self.command, 
            ", ".join(
                [
                    u'%s=%r'%(k, v)
                    for k, v in sorted(self.named.items())
                ]
            )
        )
    def __repr__(self):
        try:
            return unicode(self)
        except Exception as err:
            print err 
            return object.__repr__(self)
        
