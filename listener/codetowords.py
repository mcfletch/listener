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
    return re.sub(r'([A-Z]+)', r' \1', name).strip().split()
    
def break_down_name( name ):
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
        for fragment in fragments[:-1]:
            if fragment:
                result.extend( break_down_name(fragment))
            result.extend( ['under'] )
        if fragments[-1]:
            result.extend( break_down_name(fragments[-1]))
        return result
    possibles = parse_camel( name )
    if len(possibles) == 1:
        if possibles[0].isupper():
            return ['all','caps',possibles[0]]
        elif possibles[0].islower():
            return possibles 
        elif possibles[0][0].isupper():
            return ['cap',possibles[0]]
        else:
            raise ValueError( "Doesn't seem to be an identifier" )
    start_caps = [x for x in possibles if (x[0].isupper() and x[1:].islower())]
    if start_caps == possibles:
        return ['cap','camel']+possibles
    elif start_caps == possibles[1:]:
        return ['camel']+possibles 
    return possibles
    
def codetowords( lines ):
    """Tokenize a given line for further processing"""
    current_line = []
    new_lines = [current_line]
    for type,token,starting,ending,line in tokenize.generate_tokens( iter(lines).next ):
        if type ==tokenize.OP:
            current_line.append( OP_NAMES.get( token, token ))
        elif type == tokenize.NEWLINE:
            current_line = []
            new_lines.append( current_line )
        elif type in (tokenize.ENDMARKER,tokenize.INDENT,tokenize.DEDENT):
            pass
        elif type == tokenize.NAME:
            current_line.extend( break_down_name( token ) )
        else:
            current_line.append( token )
    return new_lines


def main():
    lines = open( sys.argv[1] ).readlines()
    import pprint
    pprint.pprint(codetowords( lines ))
