
from dataclasses import dataclass, field
from multimethod import multimeta
from typing      import Union, List, Dict
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


@dataclass
class Set(Expression):
    obj: Expression    
    ident: str          
    value: Expression  


@dataclass
class Get(Expression):
    obj: Expression    
    ident: str          


@dataclass
class This(Expression):
    pass  


@dataclass
class Super(Expression):
    ident: str          
    obj: Expression 

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
class CompoundAssignmentExpr(Expression):
    ident: str        
    opr: str          
    expr: Expression 

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
class ArraySizeExpr(Expression):
    array: str

@dataclass
class VarDeclStmt(Statement):
    ident: str
    type_: str
    expr: Expression = field(default_factory=NullStmt)

#nuevo
@dataclass
class ClassPropertyDecl(Statement):
    ident: str                           
    type_: str                         
    access: str = "public"              
    value: Expression = field(default_factory=lambda: None)
    
@dataclass
class ClassArrayPropertyDecl(Statement):
    ident: str                           
    type_: str                          
    size: Expression
    access: str = "public"              
    values: List[Expression] = field(default_factory=list) 

@dataclass
class ClassMethodDecl(Statement):
    ident : str                        
    body: CompoundStmt   
    type_: str
    params: List[VarDeclStmt] = field(default_factory=list) 
    access: str = "public"
    
@dataclass
class ClassDeclStmt(Statement):
    ident: str                 
    sclass: Union[Expression, None]  
    methods: List[ClassMethodDecl] = field(default_factory=list)      
    properties: List[ClassPropertyDecl] = field(default_factory=list)
    
@dataclass
class SuperAccess(Expression):
    ident: str

@dataclass
class SuperMethodCall(Expression):
    ident: str
    args: List[Expression] = field(default_factory=list)
    
@dataclass
class ClassInstanceCreation(Statement):
    type_: str  
    ident: str   
    constructor: str  

@dataclass
class CallMethod(Expression):
    obj: Expression    
    ident: str          
    args: List[Expression]  



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
        
    def visit(self, n: ArrayLoockupExpr, parent_tree: Tree):
        node = parent_tree.add(f"Array {n.ident} access")
        n.index.accept(self, node)
        
    def visit(self, n: ArrayAssignmentExpr, parent_tree: Tree):
        node = parent_tree.add(f"Assigment array {n.array}")
        n.index.accept(self, node)
        n.expr.accept(self, node)
            
    def visit(self, n: NullStmt, parent_tree: Tree):
        parent_tree.add(f'NullStmt')
        
    def visit(self, n: CompoundStmt, parent_tree: Tree):
        compound_node = parent_tree.add("Compound Statement")
        
        for local_decl in n.decls:
            local_decl.accept(self, compound_node)

        for stmt in n.stmts:
            stmt.accept(self, compound_node)
            
    #nuevo
    def visit(self, n: ClassDeclStmt, parent_tree: Tree):
        class_node = parent_tree.add(f'ClassDeclStmt: {n.ident}')
        if n.sclass:
            class_node.add(f'Extends: {n.sclass}')
        # Agregar propiedades
        properties_node = class_node.add('Properties')
        for prop in n.properties:
            prop.accept(self, properties_node)
        # Agregar métodos
        methods_node = class_node.add('Methods')
        for method in n.methods:
            method.accept(self, methods_node)
            
    def visit(self, n: ClassMethodDecl, parent_tree: Tree):
        method_node = parent_tree.add(f'Method: {n.ident} (Access: {n.access}) Type: {n.type_}')
        params_node = method_node.add('Parameters')
        for param in n.params:
            param.accept(self, params_node)
        method_node.add('Body')
        n.body.accept(self, method_node)

    def visit(self, n: ClassPropertyDecl, parent_tree: Tree):
        parent_tree.add(f'Property: {n.ident} (Type: {n.type_}, Access: {n.access})')
        
    def visit(self, n: ClassArrayPropertyDecl, parent_tree: Tree):
        parent_tree.add(f'ClassArrayProperty: {n.ident} (Type: {n.type_}, Size: {n.size}, Access: {n.access})')


    def visit(self, n: Set, parent_tree: Tree):
        node = parent_tree.add(f"Set: {n.ident}")
        self.visit(n.obj, node)
        self.visit(n.value, node)

    def visit(self, n: Get, parent_tree: Tree):
        node = parent_tree.add(f"Get: {n.ident}")
        self.visit(n.obj, node)

    def visit(self, n: This, parent_tree: Tree):
        parent_tree.add("This")

    def visit(self, n: Super, parent_tree: Tree):
        node = parent_tree.add(f"Super: {n.ident}")
        self.visit(n.obj, node)
        
    def visit(self, n: CompoundAssignmentExpr, parent_tree: Tree):
        """
        Representa una asignación compuesta en el árbol de representación.
        """
        compound_node = parent_tree.add(f'CompoundAssignment: {n.ident} {n.opr}')
        n.expr.accept(self, compound_node)
        
    def visit(self, n: SuperAccess, parent_tree: Tree):
        parent_tree.add(f"SuperAccess: {n.ident}")
    
    def visit(self, n: SuperMethodCall, parent_tree: Tree):
        super_call_node = parent_tree.add(f"SuperCall: {n.ident}")
        args_node = super_call_node.add("Arguments")
        for arg in n.args:
            arg.accept(self, args_node)

    def visit(self, n: ClassInstanceCreation, parent_tree: Tree):
        parent_tree.add(f"Class Instance: {n.ident} type {n.type_}")

    def visit(self, n: CallMethod, parent_tree: Tree):
        parent_tree.add(f"Call Method: {n.obj} Object: {n.ident}")
    
    def render(self, root_node):
        tree = Tree("AST")
        self.visit(root_node, tree)
        return tree