import sly
import re
from rich import print
from rich.table   import Table
from rich.console import Console

class Lexer(sly.Lexer):

    tokens = (
        # Palabras reservadas
        "CHAR", "VOID", "BOOL", "INT", "FLOAT", "IF", "ELSE", "FOR", "WHILE", "CLASS",
        "RETURN", "BREAK", "CONTINUE", "NOT", "NEW", "PRIVATE", "PUBLIC", "PROTECTED",

        # Operadores de Relacion
        "AND", "OR", "EQ", "NE", "GE", "LE",
        

        #Otros simbolos
        "IDENT", "STRING", "BOOL_LIT", "INT_LIT", "FLOAT_LIT", "CHAR_LIT",

    )
    literals = "+-*/%=()[]{}.,:;<>!&|~" 

    #patrones a ignorar
    ignore = " \t\r"
    
    # Ignorar saltos de linea
    @_(r'\n+')
    def ignore_lineno(self, t):
        self.lineno += t.value.count('\n')

    # Ignorar Comentarios
    @_(r'//.*')
    def ignore_cppcomment(self, t):
        self.lineno += 1

    @_(r'/\*([^*]|\*(?!/))*\*/')
    def ignore_comment(self, t):
        self.lineno += t.value.count('\n')


    #Definicion de tokens
    IDENT = r"[a-zA-Z_][a-zA-Z0-9_]*"
    IDENT["void"] = "VOID"
    IDENT["bool"] = "BOOL"
    IDENT["int"] = "INT"
    IDENT["float"] = "FLOAT"
    IDENT["char"] = "CHAR"
    IDENT["if"] = "IF"
    IDENT["else"] = "ELSE"
    IDENT["for"] = "FOR"
    IDENT["while"] = "WHILE"
    IDENT["class"] = "CLASS"
    IDENT["return"] = "RETURN"
    IDENT["break"] = "BREAK"
    IDENT["continue"] = "CONTINUE"
    IDENT["new"] = "NEW"
    IDENT["and"] = "AND"
    IDENT["or"] = "OR"
    IDENT["not"] = "NOT"
    IDENT["private"] = "PRIVATE"
    IDENT["public"] = "PUBLIC"
    IDENT["protected"] = "PROTECTED"
    IDENT["true"] = "BOOL_LIT"
    IDENT["false"] = "BOOL_LIT"
    # IDENT[""] = ""
    
    AND = r"&&"
    OR = r"\|\|"
    EQ = r"=="
    NE = r"!="
    LE = r"<="
    GE = r">="
    
    @_(r'"(?:[^\"\\]|\\.)*"')
    def STRING(self, t):
        tstr = t.value.replace('\\', '')
        m = re.search(r'\\[^\n]', tstr)
        if m:
            print(f"{self.lineno}: Caracter de escape '{m.group(0)}' no soportado")
            return
        return t
    
    @_(r'(?<![\w.-])(-?(?:0|[1-9][0-9]*)\.[0-9]+)(?![\w.])')
    def FLOAT_LIT(self, t):
        t.value = float(t.value)
        return t

    @_(r'(0\d+)((\.\d+(e[-+]?\d+)?)|(e[-+]?\d+))')
    def malformed_fnumber(self, t):
        print(f"{self.lineno}: Literal de punto flotante '{t.value}' no sportado")
        return None

    @_(r'(?<![\w.-])-?(?:0|[1-9][0-9]*)(?![\w.])')
    def INT_LIT(self, t):
        t.value = int(t.value)
        return t

    @_(r'0\d+')
    def malformed_inumber(self, t):
        print(f"{self.lineno}: Literal entera '{t.value}' no sportado")
        return None
    
    @_(r"'[^']'")
    def CHAR_LIT(self, t):
        return t

    def error(self, token):
        print(f"[blue]LINE {token.lineno}: ILEGAL CHARACTER [/blue][red]{token.value}[/red]")
        self.index += 1

def print_lexer(source):

    lex = Lexer()

    table = Table(title='Análisis Léxico')
    table.add_column('type')
    table.add_column('value')
    table.add_column('lineno', justify='right')

    for tok in lex.tokenize(source):
        value = tok.value if isinstance(tok.value, str) else str(tok.value)
        table.add_row(tok.type, value, str(tok.lineno))
    
    console = Console()
    console.print(table)

if __name__ == '__main__':
    
    print_lexer(open("hola.mcc", encoding='utf-8').read())