
from os.path import abspath, dirname, join
import sys

from .lexer import Lexer
from ply import lex, yacc

import inspect

pickle_file = abspath(join(dirname(__file__), 'parsetab.dat'))

if sys.version_info[0] < 3:
    def iteritems(d):
        return iter(d.iteritems())
else:
    def iteritems(d):
        return iter(d.items())


class HclParser(object):
    
    #
    # Tokens
    #
    
    tokens = (
        'BOOL',
        'NUMBER',
        'COMMA', 'IDENTIFIER', 'EQUAL', 'STRING', 'MINUS',
        'LEFTBRACE', 'RIGHTBRACE', 'LEFTBRACKET', 'RIGHTBRACKET', 'PERIOD',
        'EPLUS', 'EMINUS'
    )
    
    #
    # Yacc parser section
    #
    
    def objectlist_flat(self, lt):
        '''
            Similar to the dict constructor, but handles dups
            
            HCL is unclear on what one should do when duplicate keys are
            encountered. These comments aren't clear either:
            
            from decoder.go: if we're at the root or we're directly within
                             a list, decode into dicts, otherwise lists
                
            from object.go: there's a flattened list structure
        '''
        d = {}
        
        for k,v in lt:
            if isinstance(v, dict):
                dd = d.setdefault(k, {})
                for kk,vv in iteritems(v):
                    dd[kk] = vv
            else:
                d[k] = v
            
        return d
    
    def p_top(self, p):
        "top : objectlist"
        #self.print_p(p)
        p[0] = self.objectlist_flat(p[1])
    
    
    def p_objectlist_0(self, p):
        "objectlist : objectitem"
        #self.print_p(p)
        p[0] = [p[1]]
    
    def p_objectlist_1(self, p):
        "objectlist : objectlist objectitem"
        #self.print_p(p)
        p[0] = p[1] + [p[2]]
    
    
    def p_object_0(self, p):
        "object : LEFTBRACE objectlist RIGHTBRACE"
        #self.print_p(p)
        p[0] = self.objectlist_flat(p[2])
        
    def p_object_1(self, p):
        "object : LEFTBRACE RIGHTBRACE"
        #self.print_p(p)
        p[0] = {}
    
    
    def p_objectitem_0(self, p):
        '''
        objectitem : IDENTIFIER EQUAL number
                   | IDENTIFIER EQUAL BOOL
                   | IDENTIFIER EQUAL STRING
                   | IDENTIFIER EQUAL object
                   | IDENTIFIER EQUAL list
        '''
        #self.print_p(p)
        p[0] = (p[1], p[3])
    
    def p_objectitem_1(self, p):
        "objectitem : block"
        #self.print_p(p)
        p[0] = p[1]
    
    
    def p_block_0(self, p):
        "block : blockId object"
        #self.print_p(p)
        p[0] = (p[1], p[2])
        
    def p_block_1(self, p):
        "block : blockId block"
        #self.print_p(p)
        p[0] = (p[1], {p[2][0]: p[2][1]})
        
    def p_blockId(self, p):
        '''
        blockId : IDENTIFIER
                | STRING
        '''
        #self.print_p(p)
        p[0] = p[1]
    
    
    def p_list_0(self, p):
        "list : LEFTBRACKET listitems RIGHTBRACKET"
        #self.print_p(p)
        p[0] = p[2]
        
    def p_list_1(self, p):
        "list : LEFTBRACKET RIGHTBRACKET"
        #self.print_p(p)
        p[0] = []
        
        
    def p_listitems_0(self, p):
        "listitems : listitem"
        #self.print_p(p)
        p[0] = [p[1]]
        
    def p_listitems_1(self, p):
        "listitems : listitems COMMA listitem"
        #self.print_p(p)
        p[0] = p[1] + [p[3]]
        
        
    def p_listitem(self, p):
        '''
        listitem : number
                 | STRING
        '''
        #self.print_p(p)
        p[0] = p[1]
        
    def p_number_0(self, p):
        "number : int"
        #self.print_p(p)
        p[0] = p[1]
        
    def p_number_1(self, p):
        "number : int frac"
        #self.print_p(p)
        p[0] = float("{0}.{1}".format(p[1], p[2]))
        
    def p_number_2(self, p):
        "number : int exp"
        #self.print_p(p)
        p[0] = float("{0}{1}".format(p[1], p[2]))
        
    def p_number_3(self, p):
        "number : int frac exp"
        #self.print_p(p)
        p[0] = float("{0}.{1}{2}".format(p[1], p[2], p[3]))
        
    def p_int_0(self, p):
        "int : MINUS int"
        #self.print_p(p)
        p[0] = -p[2]
        
    def p_int_1(self, p):
        "int : NUMBER"
        #self.print_p(p)
        p[0] = p[1]
        
    def p_exp_0(self, p):
        "exp : EPLUS NUMBER"
        #self.print_p(p)
        p[0] = "e{0}".format(p[2]) 
        
    def p_exp_1(self, p):
        "exp : EMINUS NUMBER"
        #self.print_p(p)
        p[0] = "e-{0}".format(p[2])
        
    def p_frac(self, p):
        "frac : PERIOD NUMBER"
        #self.print_p(p)
        p[0] = p[2]
   
    
    # useful for debugging the parser
    #def print_p(self, p):
    #    name = inspect.getouterframes(inspect.currentframe(), 2)[1][3]
    #    print('%20s: %s' % (name, ' | '.join([str(p[i]) for i in range(0, len(p))])))
    
    
    def p_error(self, p):
        # Derived from https://groups.google.com/forum/#!topic/ply-hack/spqwuM1Q6gM
        
        #Ugly hack since Ply doesn't provide any useful error information
        try:
            frame = inspect.currentframe()
            cvars = frame.f_back.f_locals
            expected = "; expected %s" % (', '.join(cvars['actions'][cvars['state']].keys()))
        except:
            expected = ""
        
        if p is not None:
            msg = "Line %d, column %d: unexpected %s%s" % (p.lineno, p.lexpos, p.type, expected)
        else:
            msg = "Unexpected end of file%s" % expected
        
        raise ValueError(msg)
    
        
    def __init__(self):
        self.yacc = yacc.yacc(module=self, debug=False, optimize=1, picklefile=pickle_file)
        
    def parse(self, s):
        return self.yacc.parse(s, lexer=Lexer())



