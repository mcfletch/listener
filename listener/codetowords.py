"""Convert code to words in such a way that we can process into a language model

The idea here is that we scan a project, processing the (Python) code and 
producing a language model based on the transformations here. The result 
*should* be a fairly tightly constrained frequency set that we'll add as a 
heavily weighted favourite to the base (natural) language model.
"""
import re, tokenize, sys
import logging
log = logging.getLogger( __name__ )

OP_PARSER = re.compile(r'(\W+)(.+)')
def parse_op( op ):
    op = op.split('\t')[0]
    return OP_PARSER.match( op ).groups()[0], op

def _create_op_names( ):
    result = {}
    for o in [
        '!exclamation-point\tEH K S K L AH M EY SH AH N P OY N T\n',
        '"double-quote\tD AH B AH L K W OW T\n',
        '"end-of-quote\tEH N D AH V K W OW T\n',
        '"end-quote\tEH N D K W OW T\n',
        '"quote\tK W OW T\n',
        '"unquote\tAH N K W OW T\n',
        '#sharp-sign\tSH AA R P S AY N\n',
        '%percent\tP ER S EH N T\n',
        '&ampersand\tAE M P ER S AE N D\n',
        "'quote\tK W OW T\n",
        "'single-quote\tS IH NG G AH L K W OW T\n",
        #'(begin-parens\tB IH G IH N P ER EH N Z\n',
        '(left-paren\tL EH F T P ER EH N\n',
        '(open-parentheses\tOW P AH N P ER EH N TH AH S IY Z\n',
        '(paren\tP ER EH N\n',
        '(parens\tP ER EH N Z\n',
        '(parentheses\tP ER EH N TH AH S IY Z\n',
#        ')close-paren\tK L OW Z P ER EH N\n',
#        ')close-parentheses\tK L OW Z P ER EH N TH AH S IY Z\n',
#        ')end-paren\tEH N D P ER EH N\n',
#        ')end-parens\tEH N D P ER EH N Z\n',
#        ')end-parentheses\tEH N D P ER EH N TH AH S IY Z\n',
#        ')end-the-paren\tEH N D DH AH P ER EH N\n',
#        ')paren\tP ER EH N\n',
#        ')parens\tP ER EH N Z\n',
        ')right-paren\tR AY T P ER EH N\n',
        ')un-parentheses\tAH N P ER EH N TH AH S IY Z\n',
        ',comma\tK AA M AH\n',
        '-hyphen\tHH AY F AH N\n',
        #'-dash\tD AE SH\n',
        '...ellipsis\tIH L IH P S IH S\n',
        '.dot\tD AA T\n',
        '.decimal\tD EH S AH M AH L\n',
        '.full-stop\tF UH L S T AA P\n',
        '.period\tP IH R IY AH D\n',
        '.point\tP OY N T\n',
        '/slash\tS L AE SH\n',
        ':colon\tK OW L AH N\n',
        ';semi-colon\tS EH M IY K OW L AH N\n',
        '?question-mark\tK W EH S CH AH N M AA R K\n',
        '{brace\tB R EY S\n',
        '{left-brace\tL EH F T B R EY S\n',
        '}close-brace\tK L OW Z B R EY S\n',
        '}right-brace\tR AY T B R EY S\n',
        # custom...
        '[left-bracket\tL EH F T B R AE K IH T',
        ']right-bracket\tR AY T B R AE K IH T',
        '|bar\tB AA R',
        '~tilde\tT IH L D IY',
    ]:
        punc,name = parse_op( o )
        if punc not in result:
            result[punc] = name
    result.update({
        '(':'(open-paren',
        ')':')close-paren',
        '[':'[open-bracket',
        ']':']close-bracket',
        '{': '{open-brace',
        '}': '}close-brace',
        '<': '<less-than',
        '>': '>greater-than',
        ':':':colon',
        '=':'=equals',
        '==':'==equal-equal',
        '!=':'!=not-equal',
        '.': '.dot',
        ',': ',comma',
        '%': '%percent',
        '@': '@at',
        '*': '*asterisk',
        '**': '**asterisk-asterisk',
        '+': '+plus',
        '_': '_under',
        '://': ':colon /slash /slash',
        '\n': 'new-line',
        '`': '`back-tick',
        '\\': '\\back-slash',
        '^': '^caret',
        '$': '$dollar-sign',
    })

    return result
OP_NAMES = _create_op_names()

def parse_run_together( name, dictionary=None ):
    if not dictionary:
        return [name]
    # split up the name looking for runtogether words...
    name = name.lower()
    if name in dictionary:
        return [name]
    if name.isdigit():
        return [digit(n) for n in name]
    # TODO: use statistics to decide which sub-words are the most 
    # *likely* to occur, rather than always searching for a longer match...
    
    # anything smaller than 1 is *always* in the dictionary...
    prefixes = [name[:i] for i in range(1,len(name))]
    mapped = dictionary.have_words( *prefixes )
    possibles = []
    for (prefix,translations) in sorted(mapped.items(),key=lambda x: len(x[0]),reverse=True):
        if translations:
            suffix = name[len(prefix):]
            if suffix in dictionary:
                return [prefix,suffix]
            remaining = parse_run_together( suffix, dictionary )
            if len(prefix) > 1 and remaining != [suffix]:
                return [prefix]+remaining
            possibles.append( [ prefix ] + remaining )
    suffixes = [name[-i:] for i in range(1,len(name))]
    mapped = dictionary.have_words( *suffixes )
    possibles = []
    for (suffix,translations) in sorted(mapped.items(),key=lambda x: len(x[0]),reverse=True):
        if translations:
            prefix = name[:-len(suffix)]
            if prefix in dictionary:
                return [prefix,suffix]
            remaining = parse_run_together( prefix, dictionary )
            if len(suffix) > 1 and remaining != [prefix]:
                return remaining+[suffix]
            possibles.append( remaining+[suffix] )
    if len(name) < 3:
        return [(digit(c) or c) for c in name]
    return [name]

def parse_run_together_with_markup( name, dictionary ):
    base =parse_run_together( name, dictionary )
    if len(base) > 1:
        return ['no-space']+base+['spaces']
    return base
    

def parse_camel( name, dictionary=None ):
    expanded = re.sub(r'([A-Z]+|[0-9]+)', r' \1', name)
    split = expanded.strip().split()
    all_caps = [x.upper() for x in split] == split
    cap_camel_case = [x.title() for x in split] == split 
    camel_case = len(split) > 1 and [x.title() for x in split[1:]] == split[1:]
    
    words = [x for x in split if not x.isdigit()]
    split_expanded = []
    for item in split:
        if item.isdigit():
            split_expanded.extend( [digit(x) for x in item])
        else:
            split_expanded.append( item )

    run_together_expansion = sum([
        parse_run_together_with_markup(x,dictionary) 
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
def digit( c ):
    return DIGITS.get(c)
    
def break_down_name( name, dictionary=None ):
    result = []
    if name.isdigit():
        return [digit(n) for n in name]
    split = operator( name )
    if split:
        return split
    if name.startswith( '__' ) and name.endswith( '__'):
        return ['dunder'] + break_down_name( name[2:-2], dictionary=dictionary )
    elif '__' in name:
        fragments = [x for x in name.split('__')]
        for fragment in fragments[:-1]:
            if fragment:
                result.extend( break_down_name(fragment,dictionary=dictionary))
            result.extend( ['under','under'] )
        if fragments[-1]:
            result.extend( break_down_name(fragments[-1],dictionary=dictionary))
        return result
    elif '_' in name:
        fragments = [x for x in name.split('_')]
        # TODO: provide a under-name x y z -> x_y_z
        for fragment in fragments[:-1]:
            if fragment:
                result.extend( break_down_name(fragment,dictionary=dictionary))
            result.extend( ['under'] )
        if fragments[-1]:
            result.extend( break_down_name(fragments[-1],dictionary=dictionary))
        return result
    possibles = parse_camel( name, dictionary=dictionary )
    return possibles

TEXT_SPLITTER = re.compile( r"""(\w+[']\w+)|\w+|[^\w\s]+|[\n]""", re.U|re.M )
def textual_content( content, dictionary=None ):
    """Break down textual content (strings, comments) into dictation"""
    words = [x.group(0) for x in TEXT_SPLITTER.finditer(content)]
    result = []
    for word in words:
        result.extend( break_down_name( word, dictionary=dictionary ))
    return result

def operator( token ):
    if token in OP_NAMES:
        return [OP_NAMES[token]]
    elif all([t in OP_NAMES for t in token]):
        return [OP_NAMES[t] for t in token]

CODING = re.compile( r'coding[:=]\s*([-\w.]+)' )
        
def codetowords( lines, dictionary=None ):
    """Tokenize a given line for further processing"""
    current_line = []
    new_lines = [current_line]
    encoding = 'ascii'
    for type,token,starting,ending,line in tokenize.generate_tokens( iter(lines).next ):
        if type ==tokenize.OP:
            split_up = operator( token ) or [token]
            current_line.extend( split_up )
        elif type == tokenize.NEWLINE:
            current_line = []
            current_line.extend([ 'new-line'])
            new_lines.append( current_line )
        elif type == tokenize.NL:
            # newline without new source-code-line
            current_line.extend([ 'new-line'])
        elif type == tokenize.NUMBER:
            current_line.extend( [digit(x) for x in token] )
        elif type == tokenize.COMMENT:
            match = CODING.search( token )
            if match:
                encoding = match.group(1)
            current_line.extend( textual_content( token, dictionary=dictionary ))
        elif type == tokenize.STRING:
            while token and token[0].isalpha():
                current_line.append( token[0] )
                token = token[1:]
            
            for quote_type,name in [
                ('"""','"""triple-quote'),
                ("'''","'''triple-single-quote"),
                ('"', '"quote'),
                ("'", "'single-quote")
            ]:
                if token.startswith( quote_type ):
                    
                    token = token[len(quote_type):-len(quote_type)]
                    current_line.append( name )
                    current_line.extend( textual_content( 
                        token.decode(encoding), 
                        dictionary=dictionary 
                    ) )
                    current_line.append( name )
        elif type == tokenize.DEDENT:
            current_line.append( 'dedent' )
        elif type == tokenize.INDENT:
            current_line.append( 'indent' )
        elif type in (tokenize.ENDMARKER,):
            pass
        elif type == tokenize.NAME:
            current_line.extend( break_down_name( token, dictionary=dictionary ) )
        else:
            current_line.append( token )
    return new_lines


