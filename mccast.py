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
from dataclasses import dataclass, field
from multimethod import multimeta
from typing      import Union, List
from rich.tree import Tree

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
class Program(Statement):
    stmts: List[Statement] = field(default_factory=list)

@dataclass
class VarAssignmentExpr(Expression):
    ident: str
    expr: Expression

@dataclass
class ExprStmt(Statement):
    expr: Expression

@dataclass
class ElseStmt(Statement):
    body: Statement

@dataclass
class IfStmt(Statement):
    condition: Expression
    then_brach: Statement
    else_branch: Union[ElseStmt, None]
    

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
class BreakStmt(Statement):
    pass

@dataclass
class ContinueStmt(Statement):
    pass

@dataclass
class ReturnStmt(Statement):
    expr: Union[Expression, None]

@dataclass
class FunctDeclStmt(Statement):
    type_: str
    ident: str
    body: Statement
    params: List[Statement] = field(default_factory=list)

@dataclass
class StaticVarDeclStmt(Statement):
    ident: str
    type_: str
    
# =====================================================================
# Clases Concretas
# =====================================================================
@dataclass
class NullStmt(Statement):
    pass

@dataclass
class CompoundStmt(Statement):
    decls: List[Expression] = field(default_factory=list) 
    stmts: List[Statement] = field(default_factory=list)


@dataclass
class ConstExpr(Expression):
    value : Union[bool, int, float, str, None]

@dataclass
class VarAssignmentExpr(Expression):
    ident  : str
    expr : Expression

@dataclass
class VarExpr(Expression):
    ident: str

@dataclass
class ArrayLoockupExpr(Expression):
    ident: str
    index: Expression 

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
    type_: str
    ident: str
    size_expr: Expression
    value: Expression = field(default_factory=NullStmt)

@dataclass
class CallExpr(Expression):
    func_name: str
    args: List[Expression] = field(default_factory=list)

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

@dataclass
class VarDeclStmt(Statement):
    ident: str
    type_: str
    expr: Expression = field(default_factory=NullStmt)

@dataclass
class ArrayDeclStmt(Statement):
    ident: str
    type_: str

class RenderTree(Visitor):
    def __init__(self):
        self.seq = 0
        
    def _seq(self):
        self.seq += 1
        return f"n{self.seq}"
    
    def visit(self, n: Program, parent_tree: Tree):
        prog_node = parent_tree.add(f'Program')
        for stmt in n.stmts:
            stmt.accept(self, prog_node)
        return prog_node

    def visit(self, n: VarAssignmentExpr, parent_tree: Tree):
        var_node = parent_tree.add(f'VarAssignment: {n.ident}')
        n.expr.accept(self, var_node)
        
    def visit(self, n: VarDeclStmt, parent_tree: Tree):
        parent_tree.add(f'Variable Declaration: {n.type_} {n.ident} {n.expr if not isinstance(n.expr, NullStmt) else ""}')
                
    def visit(self, n: StaticVarDeclStmt, parent_tree: Tree):
        parent_tree.add(f'Var: {n.ident}')
        
    def visit(self, n: ArrayDeclStmt, parent_tree: Tree):
        parent_tree.add(f'Array Declaration: {n.ident} {n.type_}')

    def visit(self, n: ExprStmt, parent_tree: Tree):
        expr_node = parent_tree.add(f'ExprStmt')
        n.expr.accept(self, expr_node)
        
    def visit(self, n: IfStmt, parent_tree: Tree):
        if_node = parent_tree.add(f'IfStmt')
        n.condition.accept(self, if_node)
        n.then_brach.accept(self, if_node)
        if n.else_branch:
            n.else_branch.accept(self, if_node)
            
    def visit(self, n: ElseStmt, parent_tree: Tree):
        else_node = parent_tree.add("Else Statement")        
        n.body.accept(self, else_node)

    def visit(self, n: WhileStmt, parent_tree: Tree):
        while_node = parent_tree.add(f'WhileStmt')
        n.condition.accept(self, while_node)
        n.body.accept(self, while_node)

    def visit(self, n: ForStmt, parent_tree: Tree):
        for_node = parent_tree.add(f'ForStmt')
        n.for_init_stament.accept(self, for_node)
        n.condition.accept(self, for_node)
        n.step.accept(self, for_node)
        n.body.accept(self, for_node)

    def visit(self, n: ReturnStmt, parent_tree: Tree):
        return_node = parent_tree.add('ReturnStmt')
        if n.expr:
            n.expr.accept(self, return_node)
        
    def visit(self, n: BreakStmt, parent_tree: Tree):
        parent_tree.add(f'BreakStmt')

    def visit(self, n: ContinueStmt, parent_tree: Tree):
        parent_tree.add(f'ContinueStmt')

    def visit(self, n: FunctDeclStmt, parent_tree: Tree):
        func_node = parent_tree.add(f'Function: {n.ident}')
        for param in n.params:
            param.accept(self, func_node)
        n.body.accept(self, func_node)

    def visit(self, n: ConstExpr, parent_tree: Tree):
        parent_tree.add(f'ConstExpr: {n.value}')

    def visit(self, n: VarExpr, parent_tree: Tree):
        parent_tree.add(f'VarExpr: {n.ident}')
        
    def visit(self, n: BinaryOpExpr, parent_tree: Tree):
        binary_node = parent_tree.add(f'BinaryOp: {n.opr}')
        n.left.accept(self, binary_node)
        n.right.accept(self, binary_node)
        
    def visit(self, n: UnaryOpExpr, parent_tree: Tree):
        unary_node = parent_tree.add(f'UnaryOp: {n.opr}')
        n.expr.accept(self, unary_node)
        
    def visit(self, n: CallExpr, parent_tree: Tree):
        call_node = parent_tree.add(f'CallExpr: {n.func_name}')
        for arg in n.args:
            arg.accept(self, call_node)
            
    def visit(self, n: NewArrayExpr, parent_tree: Tree):
        array_node = parent_tree.add(f'New Array: {n.type_} {n.ident} {n.value if not isinstance(n.value, NullStmt) else ""}')        
        n.size_expr.accept(self, array_node)
            
    def visit(self, n: NullStmt, parent_tree: Tree):
        parent_tree.add(f'NullStmt')
        
    def visit(self, n: CompoundStmt, parent_tree: Tree):
        compound_node = parent_tree.add("Compound Statement")
        
        for local_decl in n.decls:
            local_decl.accept(self, compound_node)

        for stmt in n.stmts:
            stmt.accept(self, compound_node)
    
    def render(self, root_node):
        tree = Tree("AST")
        self.visit(root_node, tree)
        return tree