"""Convert code to words in such a way that we can process into a language model

The idea here is that we scan a project, processing the (Python) code and 
producing a language model based on the transformations here. The result 
*should* be a fairly tightly constrained frequency set that we'll add as a 
heavily weighted favourite to the base (natural) language model.
"""
import re, tokenize, sys

OP_NAMES = {
    '(':'open paren',
    ')':'close paren',
    '[':'open bracket',
    ']':'close bracket',
    '{': 'open brace',
    '}': 'close brace',
    '<': 'less than',
    '>': 'greater than',
    ':':'colon',
    '=':'equals',
    '==':'equal equal',
    '!=':'not equal',
    '.': 'dot',
    ',': 'comma',
    '%': 'percent',
    '@': 'at',
}

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

def test_names():
    for input,expected in [
        ('thisTest',['camel', 'this', 'Test']),
        ('ThisTest',['cap','camel', 'This', 'Test']),
        ('that_test',['that','under','test']),
    ]:
        result = break_down_name( input )
        assert result == expected, (input,result)
    
    
def test_tokens():
    expected = [
        (
            'test[this]',
            [['test','open bracket','this','close bracket',]]
        ),
        (
            'this.test(this,that)',
            [['this','dot','test','open paren','this','comma','that','close paren']],
        ),
        
        (
            'class Veridian(object):',
            [['class', 'cap', 'Veridian', 'open paren', 'object', 'close paren', 'colon']],
        ),
        (
            'objectReference.attributeReference = 34 * deltaValue',
            [['camel', 'object', 'Reference', 'dot', 'camel', 'attribute', 'Reference', 'equals', '34', '*', 'camel', 'delta', 'Value']],
        ),
        (
            'GLUT_SOMETHING_HERE = 0x234',
            [['all', 'caps', 'GLUT', 'under', 'all', 'caps', 'SOMETHING', 'under', 'all', 'caps', 'HERE', 'equals', '0x234']],
        ),
        (
            'class VeridianEgg:',
            [['class', 'cap', 'camel', 'Veridian', 'Egg', 'colon']],
        ),
    ]
    for line,expected in expected:
        result = codetowords([line])
        assert result == expected, (line, result)

def main():
    lines = open( sys.argv[1] ).readlines()
    import pprint
    pprint.pprint(codetowords( lines ))
