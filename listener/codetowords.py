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
        '-dash\tD AE SH\n',
        '-hyphen\tHH AY F AH N\n',
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
    })

    return result
OP_NAMES = _create_op_names()

def parse_camel( name ):
    expanded = re.sub(r'([A-Z]+)', r' \1', name)
    expanded = re.sub(r'([0-9]+)', r' \1', expanded )
    split = expanded.strip().split()
    all_caps = [x.upper() for x in split] == split
    cap_camel_case = [x.title() for x in split] == split 
    camel_case = [x.title() for x in split[1:]] == split[1:]
    words = [x for x in split if not x.isdigit()]
    split_expanded = []
    for item in split:
        if item.isdigit():
            split_expanded.extend( [digit(x) for x in item])
        else:
            split_expanded.append( item )

    if len(words) == 0:
        # e.g. numeric fragment of a name...
        pass
    elif len(words) == 1:
        if words[0].isupper():
            split_expanded = ['all','caps'] + split_expanded
        elif words[0].title() == words[0]:
            split_expanded = ['cap']+split_expanded
    else:
        if all_caps:
            split_expanded = ['all', 'caps'] + split_expanded
        elif cap_camel_case:
            split_expanded = ['cap','camel'] + split_expanded
        elif camel_case and len(split) > 1:
            split_expanded = ['camel'] + split_expanded
    return split_expanded

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
    'x':'x',
    'X':'x',
    '-':'minus',
    '+':'plus',
    'e':'e',
    '.':'.dot',
}
def digit( c ):
    return DIGITS.get(c)
    
def break_down_name( name, dictionary=None ):
    result = []
    if name.startswith( '__' ) and name.endswith( '__'):
        return ['dunder'] + break_down_name( name[2:-4] )
    elif '__' in name:
        fragments = [x for x in name.split('__')]
        for fragment in fragments[:-1]:
            if fragment:
                result.extend( break_down_name(fragment))
            result.extend( ['under','under'] )
        if fragments[-1]:
            result.extend( break_down_name(fragments[-1]))
        return result
    elif '_' in name:
        fragments = [x for x in name.split('_')]
        # TODO: provide a under-name x y z -> x_y_z
        for fragment in fragments[:-1]:
            if fragment:
                result.extend( break_down_name(fragment))
            result.extend( ['under'] )
        if fragments[-1]:
            result.extend( break_down_name(fragments[-1]))
        return result
    possibles = parse_camel( name )
    return possibles
    
def codetowords( lines, dictionary=None ):
    """Tokenize a given line for further processing"""
    current_line = []
    new_lines = [current_line]
    for type,token,starting,ending,line in tokenize.generate_tokens( iter(lines).next ):
        if type ==tokenize.OP:
            current_line.append( OP_NAMES.get( token, token ))
        elif type == tokenize.NEWLINE:
            current_line = []
            new_lines.append( current_line )
        elif type == tokenize.NUMBER:
            current_line.extend( ['number']+ [digit(x) for x in token]+['end number'] )
        elif type == tokenize.STRING:
            if token.startswith( '"""' ):
                current_line.extend( ['"""triple-quote'] )
                current_line.append( token[3:-3] )
                current_line.extend( ['"""triple-quote'] )
            elif token.startswith( "'''" ):
                current_line.extend( ["'''triple-single-quote"] )
                current_line.append( token[3:-3] )
                current_line.extend( ["'''triple-single-quote"] )
            elif token.startswith( '"' ):
                current_line.extend( ['"quote'] )
                current_line.append( token[3:-3] )
                current_line.extend( ['"quote'] )
            elif token.startswith( "'" ):
                current_line.extend( ["'single-quote"] )
                current_line.append( token[3:-3] )
                current_line.extend( ["'single-quote"] )
            else:
                current_line.append( token )
        elif type in (tokenize.ENDMARKER,tokenize.INDENT,tokenize.DEDENT):
            pass
        elif type == tokenize.NAME:
            current_line.extend( break_down_name( token, dictionary=dictionary ) )
        else:
            current_line.append( token )
    return new_lines


def main():
    lines = open( sys.argv[1] ).readlines()
    import pprint
    pprint.pprint(codetowords( lines ))
