# mccast.py
'''
Estructura del AST (básica). 

Debe agregar las clases que considere que hacen falta.

Statement
 |
 +--- NullStmt
 |
 +--- ExprStmt
 |
 +--- IfStmt
 |
 +--- WhileStmt
 |
 +--- ReturnStmt
 |
 +--- BreakStmt
 |
 +--- FuncDeclStmt
 |
 +--- StaticVarDeclStmt


Expression
 |
 +--- ConstExpr                literales bool, int y float
 |
 +--- NewArrayExpr             Arreglos recien creados
 |
 +--- CallExpr                 Llamado a function
 |
 +--- VarExpr                  Variable en lado-derecho
 |
 +--- ArrayLoockupExpr         Contenido celda arreglo
 |
 +--- UnaryOpExpr              Unarios !, +, -
 |
 +--- BinaryOpExpr             Binarios ||,&&,==,!=,<,<=,>,>=,+,-,*,/,%
 |
 +--- VarAssignmentExpr        var = expr
 |
 +--- ArrayAssignmentExpr      var[expr] = expr
 |
 +--- IntToFloatExpr           Ensanchar integer a un float
 |
 +--- ArraySizeExpr            tamaño de un arreglo
'''
from dataclasses import dataclass
from multimethod import multimeta
from typing      import Union

# =====================================================================
# Clases Abstractas
# =====================================================================
@dataclass
class Visitor(metaclass=multimeta):
    '''
    Clase abstracta del Patron Visitor
    '''
    pass

@dataclass
class Node:
    def accept(self, v:Visitor, *args, **kwargs):
        return v.visit(self, *args, **kwargs)

@dataclass
class Statement(Node):
    pass

@dataclass
class Expression(Node):
    pass

# =====================================================================
# Clases Concretas
# =====================================================================
@dataclass
class NullStmt(Statement):
    pass

@dataclass
class ConstExpr(Expression):
    value : Union[bool, int, float]

@dataclass
class VarAssignmentExpr(Expression):
    var  : str
    expr : Expression

@dataclass
class UnaryOpExpr(Expression):
    opr  : str
    expr : Expression