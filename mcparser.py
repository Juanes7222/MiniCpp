# mcparser.py
'''
Analizador Sintactico (LALR)
'''
from rich import print
from mccast import (VarAssignmentExpr, ExprStmt, NullStmt, VarDeclStmt, FunctDeclStmt, StaticVarDeclStmt, CompoundStmt, NewArrayExpr, ConstExpr, ReturnStmt, BreakStmt, 
                    BinaryOpExpr, UnaryOpExpr, ArrayAssignmentExpr, VarExpr, ArrayLoockupExpr, CallExpr, IfStmt, ElseStmt, ForStmt, WhileStmt, ArrayDeclStmt, Program, RenderTree,
                    ArraySizeExpr, ContinueStmt)
import sly

from mclex import Lexer

class Parser(sly.Parser):
    start = 'program'
    debugfile = 'minicc.txt'
    tokens = Lexer.tokens

    precedence = (
        ('left', "OR"),
        ('left', "AND"),
        ('left', "NOT"),
        ('left', "EQ", "NE"),
        ('left', '<', "LE", '>', "GE"),
        ('left', '+', '-'),
        ('left', '*', '/', '%'),
        ('right', "="),
        ('left', 'CHAR', 'FLOAT', 'INT', 'BOOL', 'VOID'),
        ('left', 'IDENT'),
        ('right', "UMINUS", "!"),
        ('right', 'ELSE')
    )
    # Definir las Reglas de la gramática

    @_("{ decl }")
    def program(self, p):
        return Program(stmts=p.decl)

    @_("var_decl")
    def decl(self, p):
        return p.var_decl

    @_("func_decl")
    def decl(self, p):
        return p.func_decl

    @_("type_spec IDENT ';'")
    def var_decl(self, p):
        return StaticVarDeclStmt(p.IDENT, p.type_spec)

    @_("type_spec IDENT '[' expr ']' ';'")
    def var_decl(self, p):
        return NewArrayExpr(p.type_spec, p.IDENT, p.expr)

    @_("VOID", "BOOL", "INT", "FLOAT", "CHAR")
    def type_spec(self, p):
        return p[0]

    @_("type_spec IDENT '(' params ')' compound_stmt")
    def func_decl(self, p):
        return FunctDeclStmt(p.type_spec, p.IDENT, p.compound_stmt, p.params)

    @_("param_list")
    def params(self, p):
        return p.param_list

    @_("param")
    def param_list(self, p):
        return [p.param] 
    
    @_("empty")
    def params(self, p):
        return []

    @_("VOID")
    def params(self, p):
        return []

    @_("param_list ',' param")
    def param_list(self, p):
        return p.param_list + [p.param] 

    @_("type_spec IDENT")
    def param(self, p):
        return VarDeclStmt(p.IDENT, p.type_spec)

    @_("type_spec IDENT '[' ']'")
    def param(self, p):
        return ArrayDeclStmt(p.IDENT, p.type_spec)

    @_("'{' local_decls stmt_list '}'")
    def compound_stmt(self, p):
        return CompoundStmt(p.local_decls, p.stmt_list)
    
    @_("local_decl local_decls")
    def local_decls(self, p):
        return [p.local_decl] + p.local_decls

    @_("empty")
    def local_decls(self, p):
        return []

    @_("type_spec IDENT ';'")
    def local_decl(self, p):
        return VarDeclStmt(p.IDENT, p.type_spec)
    
    @_("type_spec IDENT '=' expr ';'")
    def local_decl(self, p):
        return VarDeclStmt(p.IDENT, p.type_spec, p.expr)

    @_("type_spec IDENT '[' expr ']' ';'")
    def local_decl(self, p):
        return NewArrayExpr(p.type_spec, p.IDENT, p.expr)
    
    @_("type_spec IDENT '[' expr ']' '=' '{' expr_list '}' ';'")
    def local_decl(self, p):
        return NewArrayExpr(p.type_spec, p.IDENT, p.expr, p.expr_list)
    
    @_("expr")
    def expr_list(self, p):
        return [p.expr]

    @_("expr_list ',' expr")
    def expr_list(self, p):
        return p.expr_list + [p.expr]


    @_("{ stmt }")
    def stmt_list(self, p):
        return p.stmt

    @_("expr_stmt", "compound_stmt", "if_stmt", "while_stmt", "return_stmt", "break_stmt", "for_stmt")
    def stmt(self, p):
        return p[0]

    @_("expr ';'")
    def expr_stmt(self, p):
        return ExprStmt(p.expr)

    @_("';'")
    def expr_stmt(self, p):
        return NullStmt()

    @_("WHILE '(' expr ')' stmt")
    def while_stmt(self, p):
        return WhileStmt(p.expr, p.stmt)

    @_("FOR '(' for_init_stmt ';' [ expr ] ';' [ expr ] ')' stmt")
    def for_stmt(self, p):
        return ForStmt(p.for_init_stmt, p.expr0, p.expr1, p.stmt)

    @_("var_decl")
    def for_init_stmt(self, p):
        return p.var_decl

    @_("expr_stmt")
    def for_init_stmt(self, p):
        return p.expr_stmt
    
    @_("IF '(' expr ')' stmt ELSE stmt")
    def if_stmt(self, p):
        return IfStmt(p.expr, p.stmt0, ElseStmt(p.stmt1))
    
    @_("IF '(' expr ')' stmt %prec ELSE")
    def if_stmt(self, p):
        return IfStmt(p.expr, p.stmt, None)

    @_("RETURN [ expr ] ';'")
    def return_stmt(self, p):
        return ReturnStmt(p.expr)

    @_("BREAK ';'")
    def break_stmt(self, p):
        return BreakStmt()

    @_("CONTINUE ';'")
    def break_stmt(self, p):
        return ContinueStmt()

    @_("IDENT '=' expr")
    def expr(self, p):
        return VarAssignmentExpr(p.IDENT, p.expr)

    @_("IDENT '[' expr ']' '=' expr")
    def expr(self, p):
        return ArrayAssignmentExpr(p.IDENT, p.expr0, p.expr1)

    @_("expr OR expr",
       "expr AND expr",
       "expr NOT expr",
       "expr EQ expr",
       "expr NE expr",
       "expr LE expr",
       "expr GE expr",
       "expr '<' expr",
       "expr '>' expr",
       "expr '+' expr",
       "expr '-' expr",
       "expr '*' expr",
       "expr '/' expr",
       "expr '%' expr")
    def expr(self, p):
        return BinaryOpExpr(p[1], p.expr0, p.expr1)

    @_("'!' expr", "'-' expr %prec UMINUS", "'+' expr %prec UMINUS")
    def expr(self, p):
        return UnaryOpExpr(p[0], p.expr)

    @_("'(' expr ')'")
    def expr(self, p):
        return p.expr

    @_("IDENT")
    def expr(self, p):
        return VarExpr(p.IDENT)

    @_("IDENT '[' expr ']'")
    def expr(self, p):
        return ArrayLoockupExpr(p.IDENT, p.expr)

    @_("IDENT '(' args ')'")
    def expr(self, p):
        return CallExpr(p.IDENT, p.args)

    @_("IDENT '.' SIZE")
    def expr(self, p):
        return ArraySizeExpr(p.IDENT)

    @_("BOOL_LIT", "INT_LIT", "FLOAT_LIT", "STRING", "CHAR_LIT")
    def expr(self, p):
        return ConstExpr(p[0])

    @_("NEW type_spec '[' expr ']'")
    def expr(self, p):
        return NewArrayExpr(p.type_spec, p.expr)

    @_("arg_list")
    def args(self, p):
        return p.arg_list 
    
    @_("empty")
    def args(self, p):
        return []

    @_("arg_list ',' expr")
    def arg_list(self, p):
        return p.arg_list + [p.expr]
    
    @_("expr")
    def arg_list(self, p):
        return [p.expr]

    @_("")
    def empty(self, p):
        pass

    def error(self, p):
        lineno = p.lineno if p else 'EOF'
        value  = p.value  if p else 'EOF'
        print(f"Línea {lineno}: Error de sintaxis en '{value}'")

def gen_ast(source):
    lex = Lexer()
    pas = Parser()

    tokens = lex.tokenize(source)
    # print(list(tokens))
    
    ast = pas.parse(tokens)
    if ast:
        render_tree = RenderTree()
        render_tree.render(ast)
        return render_tree
    else:
        print("[red]No se ha creado el arbol[/red]")

if __name__ == '__main__':
    import sys
    # if len(sys.argv) != 2:
    #     print(f"[red]Usage mclex.py textfile[/red]")
    #     exit(1)
        
    # parse(open(sys.argv[1], encoding='utf-8').read())
    gen_ast(open("isqrt.mcc", encoding='utf-8').read())
