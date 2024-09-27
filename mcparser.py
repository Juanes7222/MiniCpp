# mcparser.py
'''
Analizador Sintactico (LALR)
'''
from rich import print
import sly

from mclex import Lexer

class Parser(sly.Parser):
    debugfile = 'minicc.txt'

    tokens = Lexer.tokens

    precedence = (
        ('left', "OR"),
        ('left', "AND"),
        ('left', "NOT"),
        ('right', "="),
        ('left', "EQ", "NE"),
        ('left', '<', "LE", '>', "GE"),
        ('left', '+', '-'),
        ('left', '*', '/', '%'),
        ('left', 'CLASS', 'CHAR', 'FLOAT', 'INT', 'BOOL', 'VOID'),
        ('left', 'IDENT'),
        ('right', "UMINUS", "!"),
        ('right', 'ELSE')
    )
    # Definir las Reglas de la gramática

    @_("{ decl }")
    def program(self, p):
        '''
        program ::= decl+
        '''
    
    @_("var_decl", "func_decl", "class_decl")
    def decl(self, p):
        '''
        decl ::= var_decl | func_decl | class_decl
        '''

    @_("type_spec IDENT ';'")
    def var_decl(self, p):
        '''
        var_decl ::=  type_spec IDENT ';'
        '''

    @_("type_spec IDENT '[' ']' ';'")
    def var_decl(self, p):
        '''
        var_decl ::=  type_spec IDENT '[' ']' ';'
        '''

    @_("VOID", "BOOL", "INT", "FLOAT", "CHAR")
    def type_spec(self, p):
        '''
        type_spec ::= VOID | BOOL  | INT | FLOAT | CHAR
        '''

    @_("type_spec IDENT '(' params ')' compound_stmt")
    def func_decl(self, p):
        '''
        func_decl ::= type_spec IDENT '(' params ')' compound_stmt
        '''

    @_("param_list", "VOID")
    def params(self, p):
        '''
        params ::= param_list | VOID
        '''

    @_("param { ',' param }")
    def param_list(self, p):
        '''
        param_list ::= param ( ',' param )*
        '''

    @_("type_spec IDENT")
    def param(self, p):
        '''
        param ::= type_spec IDENT
        '''

    @_("type_spec IDENT '[' ']'")
    def param(self, p):
        '''
        param ::= type_spec IDENT '[' ']'
        '''

    @_("'{' local_decls stmt_list '}'")
    def compound_stmt(self, p):
        '''
        compound_stmt ::= '{' local_decls stmt_list '}'
        '''
    
    @_("local_decl", "empty")
    def local_decls(self, p):
        '''
        local_decls ::= local_decl |
        '''

    @_("type_spec IDENT ';'")
    def local_decl(self, p):
        '''
        local_decl ::= type_spec IDENT ';'
        '''

    @_("type_spec IDENT '[' ']' ';'")
    def local_decl(self, p):
        '''
        local_decl ::= type_spec IDENT '[' ']' ';'
        '''

    @_("{ stmt }")
    def stmt_list(self, p):
        '''
        stmt_list ::= stmt*
        '''

    @_("expr_stmt", "compound_stmt", "if_stmt", "while_stmt", "return_stmt", "break_stmt", "for_stmt")
    def stmt(self, p):
        '''
        stmt ::= expr_stmt | compound_stmt | if_stmt | while_stmt | return_stmt | break_stmt | for_stmt
        '''

    @_("expr ';'")
    def expr_stmt(self, p):
        '''
        expr_stmt ::= expr ';'
        '''

    @_("';'")
    def expr_stmt(self, p):
        '''
        expr_stmt ::= ';'
        '''

    @_("WHILE '(' expr ')' stmt")
    def while_stmt(self, p):
        '''
        while_stmt ::= WHILE '(' expr ')' stmt
        '''

    @_("FOR '(' for_init_stmt ';' [ expr ] ';' [ expr ] ')' stmt")
    def for_stmt(self, p):
        """for_stmt ::= 'FOR' '(' for_init_stmt expr? ';' expr? ')' stmt"""

    @_("var_decl")
    def for_init_stmt(self, p):
        """for_init_stmt ::= var_decl"""

    @_("expr_stmt")
    def for_init_stmt(self, p):
        """for_init_stmt ::= expr_stmt"""

    @_("IF '(' expr ')' stmt ELSE stmt")
    def if_stmt(self, p):
        '''
        if_stmt ::= IF '(' expr ')' stmt ( ELSE stmt )?
        '''

    # @_("IF '(' expr ')' stmt")
    # def if_stmt(self, p):
    #     '''
    #     if_stmt ::= IF '(' expr ')' stmt
    #     '''

    @_("RETURN [ expr ] ';'")
    def return_stmt(self, p):
        '''
        return_stmt ::= RETURN expr? ';'
        '''

    @_("BREAK ';'", "CONTINUE ';'")
    def break_stmt(self, p):
        '''
        break_stmt ::= ( BREAK | CONTINUE ) ';'
        '''


    @_("IDENT '=' expr")
    def expr(self, p):
        '''
        expr ::= IDENT '=' expr
        '''

    @_("IDENT '[' expr ']' '=' expr")
    def expr(self, p):
        '''
        expr ::= IDENT '[' expr ']' '=' expr
        '''

    @_("expr OR expr",
       "expr AND expr",
       "expr NOT expr",
       "expr EQ expr",
       "expr NE expr",
       "expr LE expr",
       "expr '<' expr",
       "expr GE expr",
       "expr '>' expr",
       "expr '+' expr",
       "expr '-' expr",
       "expr '*' expr",
       "expr '/' expr",
       "expr '%' expr")
    def expr(self, p):
        '''
        expr ::=  expr 'OR' expr
            | expr 'AND' expr
            | expr 'EQ' expr | expr 'NE' expr
            | expr 'LE' expr | expr '<' expr | expr 'GE' expr | expr '>' expr
            | expr '+' expr | expr '-' expr
            | expr '*' expr | expr '/' expr | expr '%' expr
        '''

    @_("'!' expr", "'-' expr %prec UMINUS", "'+' expr %prec UMINUS")
    def expr(self, p):
        '''
        expr ::= '!' expr | '-' expr | '+' expr
        '''

    @_("'(' expr ')'")
    def expr(self, p):
        '''
        expr ::= '(' expr ')'
        '''

    @_("IDENT")
    def expr(self, p):
        '''
        expr ::= IDENT
        '''

    @_("IDENT '[' expr ']'")
    def expr(self, p):
        '''
        expr ::= IDENT '[' expr ']'
        '''

    @_("IDENT '(' args ')'")
    def expr(self, p):
        '''
        expr ::= IDENT '(' args ')'
        '''

    # @_("IDENT '.' SIZE")
    # def expr(self, p):
    #     '''
    #     expr ::= IDENT '.' SIZE
    #     '''

    @_("BOOL_LIT", "INT_LIT", "FLOAT_LIT", "STRING", "CHAR_LIT")
    def expr(self, p):
        '''
        expr ::= BOOL_LIT | INT_LIT | FLOAT_LIT | STRING
        '''

    @_("NEW type_spec '[' expr ']'")
    def expr(self, p):
        '''
        expr ::= NEW type_spec '[' expr ']'
        '''

    @_("arg_list", "empty")
    def args(self, p):
        '''
        args ::= arg_list |
        ''' 

    @_("expr [ ',' expr ]")
    def arg_list(self, p):
        '''
        arg_list ::= expr ( ',' expr )*
        '''

    @_("CLASS IDENT '{' class_body '}' ';'")
    def class_decl(self, p):
        """class_decl ::= 'CLASS' 'IDENT' '{' class_body '}' ';'"""

    @_("{ class_member }")
    def class_body(self, p):
        """class_body ::= class_member*"""

    @_("access_specifier ':' { class_member_stmt }")
    def class_member(self, p):
        """class_member ::= class_member_stmt 
        """
    
    @_("func_decl")
    def class_member_stmt(self, p):
        """"""

    @_("var_decl")
    def class_member_stmt(self, p):
        """"""


    # @_("constructor_decl")
    # def class_member(self, p):
    #     """class_member ::= var_decl 
    #     | func_decl 
    #     | constructor_decl 
    #     | destructor_decl 
    #     | access_specifier ':' class_member*
    #     """

    # @_("IDENT '(' params ')' compound_stmt")
    # def constructor_decl(self, p):
    #     """constructor_decl ::= 'IDENT' '(' params ')' compound_stmt"""

    @_("PRIVATE", 'PROTECTED', 'PUBLIC')
    def access_specifier(self, p):
        """access_specifier ::= 'PRIVATE' | 'PROTECTED' | 'PUBLIC'"""

    @_("")
    def empty(self, p):
        pass

    def error(self, p):
        if p:
            print(f"Línea {p.lineno} error de sintaxis en '{p.value}' ({p.type})")
            # Just discard the token and tell the parser it's okay.
            self.errok()
        else:
            print("error de sintaxis en EOF")

def parse(source):
    lex = Lexer()
    pas = Parser()

    pas.parse(lex.tokenize(source))

if __name__ == '__main__':
    import sys

    if len(sys.argv) != 2:
        print(f"Usage mclex.py textfile")
        exit(1)

    # parse(open(sys.argv[1], encoding='utf-8').read())
    parse(open("hola.mcc", encoding='utf-8').read())
