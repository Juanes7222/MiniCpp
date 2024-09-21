import sly
from rich import print

class Lexer(sly.Lexer):

    tokens = (
        # Palabras reservadas
        "CHAR", "VOID", "BOOL", "INT", "FLOAT", "IF", "ELSE", "FOR", "WHILE", "CLASS",
        "RETURN", "BREAK", "CONTINUE", "NEW", "AND", "OR", "NOT", "PRIVATE", "PUBLIC", "PROTECTED",

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
    @_(r'//.*\n')
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

    @_(r'\"(\\.|[^\"\\])*\"')
    def STRING(self, t):
        return t
    
    @_(r'\'(\\.|[^\"\\])\'')
    def CHAR_LIT(self, t):
        return t

    @_(r"[+-]?(\d*\.\d+|\d+\.\d*)([eE][+-]?\d+)?")
    def FLOAT_LIT(self, t):
        t.value = float(t.value)
        return t

    @_(r'[+-]?\d+')
    def INT_LIT(self, t):
        t.value = int(t.value)
        return t

    def error(self, token):
        print(f"[blue]LINE {token.lineno}: ILEGAL CHARACTER [/blue][red]{token.value[0]}[/red]")
        self.index += 1

if __name__ == "__main__":
    l = Lexer()
    d = '''
    class MyClass {
            private:
                int secretVar;
            public:
                MyClass() {}
                void myMethod() {
                    float x = 1.0;
                }
            protected:
                void protectedMethod() {}
        }
'''
    
    for tok in l.tokenize(d):
        print(tok)