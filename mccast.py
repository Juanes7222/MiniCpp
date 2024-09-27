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

@dataclass
class VarAssignmentExpr(Expression):
    var: str
    expr: Expression

@dataclass
class ExprStmt(Statement):
    expr: Expression

@dataclass
class IfStmt(Statement):
    condition: Expression
    then_brach: Statement
    else_branch: Union[Statement, None]

@dataclass
class WhileStmt(Statement):
    condition: Expression
    body: Statement

@dataclass
class ForStmt(Statement):
    for_init_stament: Union[VarAssignmentExpr, ExprStmt]
    condition: Expression
    step: Expression
    body: Statement

@dataclass
class BrakeStmt(Statement):
    pass

@dataclass
class ReturnStmt(Statement):
    expr: Union[Expression, None]

@dataclass
class FunctDecltmt(Statement):
    name: str
    params: list
    body: Statement

@dataclass
class StaticVarDeclStmt(Statement):
    var_name: str
    var_type: str
    
@dataclass
class ClassMemberStmt(Statement):
    access_specifier: str
    body: Union[FunctDecltmt, VarAssignmentExpr]

@dataclass 
class ClassDeclStmt(Statement):
    name: str
    class_member: ClassMemberStmt

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

@dataclass
class BinaryOpExpr(Expression):
    opr: str
    left: Expression
    right: Expression

@dataclass
class NewArrayExpr(Expression):
    array_type: str
    size_expr: Expression

@dataclass
class CallExpr(Expression):
    func_name: str
    args: list 

@dataclass
class VarExpr(Expression):
    name: str

@dataclass
class ArrayAssignmentExpr(Expression):
    array: str
    index: Expression
    expr: Expression

@dataclass
class IntToFloatExpr(Expression):
    expr: Expression

@dataclass
class ArraySizeExpr(Expression):
    array: str