# conterp.py
'''
Tree-walking interpreter
'''
from collections import ChainMap
from rich import print

from mccast import *
from mchecker import Checker
from mcbuiltins import builtins, consts, Scanf
from mctypesys import check_binary_op, check_unary_op


# Veracidad en MiniC
def _is_truthy(value):
    if isinstance(value, bool):
        return value
    elif value is None:
        return False
    else:
        return True


class ReturnException(Exception):
    def __init__(self, value):
        self.value = value


class BreakException(Exception):
    pass


class ContinueException(Exception):
    pass


class MiniCExit(BaseException):
    pass


class AttributeError(Exception):
    pass


class Function:

    def __init__(self, node, env):
        self.node = node
        self.env = env

    @property
    def arity(self) -> int:
        return len(self.node.params)

    def __call__(self, interp, *args):
        newenv = self.env.new_child()
        for name, arg in zip(self.node.params, args):
            newenv[name.ident] = arg

        oldenv = interp.env
        interp.env = newenv
        try:
            self.node.body.accept(interp)
            result = None
        except ReturnException as e:
            result = e.value
        finally:
            interp.env = oldenv
        return result

    def bind(self, instance):
        env = self.env.new_child()
        env['this'] = instance
        return Function(self.node, env)


class Class:

    def __init__(self, name, sclass, methods):
        self.name = name
        self.sclass = sclass
        self.methods = methods

    def __str__(self):
        return self.name

    def __call__(self, *args):
        this = Instance(self)
        init = self.find_method('init')
        if init:
            init.bind(this)(*args)
        return this

    def find_method(self, name):
        meth = self.methods.get(name)
        if meth is None and self.sclass:
            return self.sclass.find_method(name)
        return meth


class Instance:

    def __init__(self, klass):
        self.klass = klass
        self.data = {}

    def __str__(self):
        return self.klass.name + " instance"

    def get(self, name):
        if name in self.data:
            return self.data[name]
        method = self.klass.find_method(name)
        if not method:
            raise AttributeError(f'Propiedad indefinida {name}')
        return method.bind(self)

    def set(self, name, value):
        self.data[name] = value


class Interpreter(Visitor):

    def __init__(self, ctxt):
        self.ctxt = ctxt
        self.env = ChainMap()
        self.check_env = ChainMap()
        self.localmap = {}

    def _check_numeric_operands(self, node, left, right):
        if isinstance(left, (int, float)) and isinstance(right, (int, float)):
            return True
        else:
            self.error(node, f"En '{node.opr}' los operandos deben ser numeros")

    def _check_numeric_operand(self, node, value):
        if isinstance(value, (int, float)):
            return True
        else:
            self.error(node, f"En '{node.op}' el operando debe ser un numero")

    def error(self, position, message):
        self.ctxt.error(position, message)
        raise MiniCExit()

    # Punto de entrada alto-nivel
    def interpret(self, node):

        for name, cval in consts.items():
            self.check_env[name] = cval
            self.env[name] = cval

        for name, func in builtins.items():
            self.check_env[name] = func
            self.env[name] = func

        try:
            Checker.check(node, self.check_env, self)
            if not self.ctxt.have_errors:
                node.accept(self)
                return self.env
        except MiniCExit as e:
            pass
        
    def call(self, func: Function, *args):
        
        if not isinstance(func, Function):
            raise RuntimeError(f"'{func.node.ident}' no es una función válida")

        # Llamar a la función con los argumentos proporcionados
        return func(self, *args)
    # Declarations

    

 

    def visit(self, node: Program):
        for stmt in node.stmts:
            stmt.accept(self)

    def visit(self, node: FunctDeclStmt):
        self.env[node.ident] = Function(node, self.env)

    def visit(self, node: VarDeclStmt):
        value = node.expr.accept(self) if node.expr else None
        self.env[node.ident] = value

    def visit(self, node: StaticVarDeclStmt):
        value = None
        self.env[node.ident] = value

    def visit(self, node: ClassDeclStmt):
        methods = {meth.ident: Function(meth, self.env)
                   for meth in node.methods}
        if node.sclass:
            if not node.sclass in self.env:
                raise RuntimeError(f"Class {node.sclass} not found")
        # sclass = node.sclass.accept(self) if node.sclass else None
        self.env[node.ident] = Class(node.ident, self.env.get(node.sclass), methods)

    def visit(self, node: CompoundStmt):
        self.env = self.env.new_child()
        for decl in node.decls:
            decl.accept(self)
        for stmt in node.stmts:
            stmt.accept(self)
        # self.env = self.env.parents

    def visit(self, node: ExprStmt):
        node.expr.accept(self)

    def visit(self, node: IfStmt):
        condition = node.condition.accept(self)
        if _is_truthy(condition):
            node.then_brach.accept(self)
        elif node.else_branch:
            node.else_branch.body.accept(self)

    def visit(self, node: WhileStmt):
        while _is_truthy(node.condition.accept(self)):
            try:
                node.body.accept(self)
            except BreakException:
                break
            except ContinueException:
                continue

    def visit(self, node: ForStmt):
        node.for_init_stament.accept(self)
        while _is_truthy(node.condition.accept(self)):
            try:
                node.body.accept(self)
                node.step.accept(self)
            except BreakException:
                break
            except ContinueException:
                continue

    def visit(self, node: BreakStmt):
        raise BreakException()

    def visit(self, node: ContinueStmt):
        raise ContinueException()

    def visit(self, node: ReturnStmt):
        value = node.expr.accept(self) if node.expr else None
        raise ReturnException(value)

    def visit(self, node: Print):
        value = node.expr.accept(self)
        print(value)

    def visit(self, node: ConstExpr):
        return node.value

    def visit(self, node: VarExpr):
        return self.env[node.ident]

    def visit(self, node: VarAssignmentExpr):
        value = node.expr.accept(self)
        self.env[node.ident] = value
        return value

    def visit(self, node: CompoundAssignmentExpr):
        current = self.env[node.ident.ident]
        value = node.expr.accept(self)
        if node.opr == "+=":
            self.env[node.ident.ident] = current + value
        elif node.opr == "-=":
            self.env[node.ident.ident] = current - value
        elif node.opr == "*=":
            self.env[node.ident.ident] = current * value
        elif node.opr == "/=":
            self.env[node.ident.ident] = current / value
        return self.env[node.ident.ident]

    def visit(self, node: BinaryOpExpr):
        left = node.left.accept(self)
        right = node.right.accept(self)
        current_name = None
        if isinstance(node.left, VarAssignmentExpr):
            current_name = node.left.ident
        elif isinstance(node.right, VarAssignmentExpr):
            current_name = node.right.ident
        if node.opr == "+":
            value = left + right
        elif node.opr == "-":
            value = left - right
        elif node.opr == "*":
            value =  left * right
        elif node.opr == "/":
            value = left / right
        elif node.opr == "==":
            value = left == right
        elif node.opr == "!=":
            value = left != right
        elif node.opr == "<":
            value = left < right
        elif node.opr == ">":
            value = left > right
        elif node.opr == "<=":
            value = left <= right
        elif node.opr == ">=":
            value = left >= right
        else:
            raise NotImplementedError(f"Operador desconocido {node.opr}")
        if current_name:
            self.env[current_name] = value
        return value

    def visit(self, node: LogicalOpExpr):
        left = node.left.accept(self)
        if node.op == "&&":
            return left and node.right.accept(self)
        elif node.op == "||":
            return left or node.right.accept(self)
        else:
            raise NotImplementedError(f"Operador lógico desconocido {node.op}")

    def visit(self, node: UnaryOpExpr):
        value = node.expr.accept(self)
        if node.opr == "-":
            self.env[node.expr.ident] += -value
            return -value
        elif node.opr == "!":
            self.env[node.expr.ident] += not _is_truthy(value)
            return not _is_truthy(value)
        elif node.opr == "++":
            self.env[node.expr.ident] += 1
            return value + 1
        elif node.opr == "--":
            self.env[node.expr.ident] -= 1
            return value - 1
        else:
            raise NotImplementedError(
                f"Operador unario desconocido {node.opr}")

    def visit(self, node: CallExpr):
        # Obtener la función del entorno
        func = self.env[node.func_name]
        
        # Si la función es scanf, maneja los argumentos de manera especial
        if isinstance(func, Scanf):
            # El primer argumento (el formato) se evalúa normalmente
            format_arg = node.args[0].accept(self)
            
            # Los siguientes argumentos son nombres de variables (referencias)
            var_args = [arg.ident for arg in node.args[1:] if isinstance(arg, VarExpr)]
            
            # Llama a scanf pasando el entorno y las variables
            return func(self.env, format_arg, *var_args)
        
        # Para otras funciones, evalúa los argumentos normalmente
        args = [arg.accept(self) for arg in node.args]
        return func(self, *args)



    def visit(self, node: ArrayLoockupExpr):
        array = self.env[node.ident]
        index = node.index.accept(self)
        return array[index]

    def visit(self, node: ArrayAssignmentExpr):
        array = self.env[node.array]
        index = node.index.accept(self)
        value = node.expr.accept(self)
        array[index] = value
        return value

    def visit(self, node: Get):
        obj = node.obj.accept(self)
        return obj.get(node.ident)

    def visit(self, node: Set):
        obj = node.obj.accept(self)
        value = node.value.accept(self)
        obj.set(node.ident, value)
        return value

    def visit(self, node: This):
        return self.env["this"]

    def visit(self, node: Super):
        sclass = self.env["super"]
        return sclass.find_method(node.ident).bind(self.env["this"])
    
    def visit(self, n: ClassInstanceCreation, env: ChainMap):
        """
        Maneja la instanciación de clases.
        """
        # Verificar que la clase existe en el entorno
        if n.type_ not in self.env:
            self.error(n, f"La clase '{n.type_}' no está definida")

        # Obtener la clase desde el entorno
        klass = self.env[n.type_]

        # Crear una instancia de la clase
        instance = Instance(klass)

        # Registrar la instancia en el entorno actual
        self.env[n.ident] = instance

        # Invocar el constructor, si está definido
        constructor = klass.find_method(n.constructor)
        if constructor:
            # Llamar al constructor con un entorno ligado a la instancia
            constructor.bind(instance).call([])
            
    def visit(self, n: NullStmt):
        pass

