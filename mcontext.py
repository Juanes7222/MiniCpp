# mcontext.py
'''
Clase de nivel superior que contiene todo sobre el 
analisis/ejecucion de un programa en Mini-C++

Sirve como repositorio de información sobre el programa,
inluido el codigo fuente, informe de errores, etc.
'''
from rich     import print
from rich.console import Console
from rich.table import Table
from collections import ChainMap
from mccast    import *
from mclex    import Lexer
from mcparser import Parser
from mchecker import Checker
from mctypes import ClassType
from mcinterp import Interpreter

class Context:
    def __init__(self):
        self.lexer  = Lexer()
        self.parser = Parser()
        self.source = ''
        self.ast    = None
        self.have_errors = False
        self.localmap = {}  # Mapa de variables locales o nodos
        self.ctxt = self  # Referencia al propio contexto para manejo de errores
        self.env = None
        
    def parse(self, source):
        self.have_errors = False
        self.source = source
        self.ast = self.parser.parse(self.lexer.tokenize(self.source))
    
    def run(self):
        if not self.have_errors:
            self.env = ChainMap()
            try:
                interpreter = Interpreter(self)
                self.env = interpreter.interpret(self.ast)
                main_function = self.env.get("main")
                if not main_function:
                    print("Error: No se definió una función 'main'")
                    return

                print("\n--- Ejecutando Programa ---")
                interpreter.call(main_function, self.env)
            except Exception as e:
                print(f"Error durante la ejecución: {e}")
                self.have_errors = True
    
    def find_source(self, node):
        indices = self.parser.index_position(node)
        if indices:
            return self.source[indices[0]:indices[1]]
        else:
            return f"{type(node).__name__} (fuente no disponible)"
    
    def error(self, position, message):
        if isinstance(position, Node):
            lineno = self.parser.line_position(position)
            (start, end) = (part_start, part_end) = self.parser.index_position(position)
            while start >= 0 and self.source[start] != '\n':
                start -= 1

            start += 1
            while end < len(self.source) and self.source[end] != '\n':
                end += 1
            print()
            print(self.source[start:end])
            print(" "*(part_start - start), end='')
            print("^"*(part_end - part_start))
            print(f"{lineno}: {message}")
        else:
            print(f"{position}: {message}")
        self.have_errors = True

def extract_symbol_info(name, info):
    """
    Extrae la información relevante del símbolo, incluyendo tipo y clase.
    """
    if isinstance(info, dict):
        symbol_type = info.get('type', 'desconocido')
        symbol_kind = info.get('kind', 'variable')
        return symbol_type, symbol_kind
    elif isinstance(info, FunctDeclStmt):
        param_list = ", ".join([f"{p.ident}: {p.type_}" for p in info.params])
        func_type = f"{info.type_} ({param_list})"
        return func_type, 'función'
    elif isinstance(info, VarDeclStmt):
        return info.type_, 'variable'
    elif isinstance(info, StaticVarDeclStmt):
        return info.type_, 'variable estática'
    elif isinstance(info, ArrayDeclStmt):
        return f"array<{info.type_}>", 'Array'
    elif isinstance(info, NewArrayExpr):
        return f"array<{info.type_}>", 'Array'
    elif isinstance(info, ClassType):
        return f"Clase", f"Miembros: {len(info.members)}"

    else:
        return 'desconocido', 'desconocido'


def print_symbol_table(env: ChainMap):
    """
    Muestra la tabla de símbolos actual (entorno) usando rich.
    """
    console = Console()

    table = Table(title="Tabla de Símbolos")

    table.add_column("Nombre", style="cyan", no_wrap=True)
    table.add_column("Tipo", style="magenta")
    table.add_column("Clase", style="green")

    for scope in env.maps:
        for name, info in scope.items():
            # Extraer información básica del símbolo
            symbol_type, symbol_kind = extract_symbol_info(name, info)
            
            # Si es una clase, mostrar sus miembros
            if isinstance(info, ClassType):
                table.add_row(name, "Clase", symbol_kind)
                for member_name, member_info in info.members.items():
                    member_type, member_kind = extract_symbol_info(member_name, member_info)
                    table.add_row(f"  {member_name}", member_type, member_kind)
            else:
                table.add_row(name, symbol_type, symbol_kind)

    console.print(table)