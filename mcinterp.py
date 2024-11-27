# conterp.py
'''
Tree-walking interpreter
'''
from collections import ChainMap
from rich import print

from mccast import *
from mchecker import Checker
from mcbuiltins import builtins, consts, CallError
from mctypes import CObject, Number, String, Bool, Nil, Array


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
            self.error(node, f"En '{node.op}' los operandos deben ser numeros")

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
        """
        Invoca una función definida en el entorno actual.
        """
        # Buscar la función en el entorno
        # if function_name not in self.env:
        #     raise RuntimeError(f"La función '{function_name}' no está definida")
        
        # func = self.env[function_name]
        if not isinstance(func, Function):
            raise RuntimeError(f"'{func.node.ident}' no es una función válida")

        # Llamar a la función con los argumentos proporcionados
        return func(self, *args)
    # Declarations

    # def visit(self, node: ClassDeclStmt):
    #     if node.sclass:
    #         sclass = node.sclass.accept(self)
    #         env = self.env.new_child()
    #         env['super'] = sclass
    #     else:
    #         sclass = None
    #         env = self.env
    #     methods = {}
    #     for meth in node.methods:
    #         methods[meth.ident] = Function(meth, env)
    #     cls = Class(node.ident, sclass, methods)
    #     self.env[node.ident] = cls

    # def visit(self, node: FunctDeclStmt):
    #     func = Function(node, self.env)
    #     self.env[node.ident] = func

    def visit(self, node: VarDeclStmt):
        if node.expr:
            expr = node.expr.accept(self)
        else:
            expr = None
        self.env[node.ident] = expr

    # Statements

    def visit(self, node: CompoundStmt):
        self.env = self.env.new_child()
        for stmt in node.stmts:
            stmt.accept(self)
        self.env = self.env.parents

    def visit(self, node: Print):
        expr = node.expr.accept(self)
        if isinstance(expr, str):
            expr = expr.replace('\\n', '\n')
            expr = expr.replace('\\t', '\t')
        print(expr, end='')

    def visit(self, node: WhileStmt):
        while _is_truthy(node.expr.accept(self)):
            try:
                node.stmt.accept(self)
            except BreakException:
                return
            except ContinueException:
                raise NotImplementedError

    def visit(self, node: IfStmt):
        expr = node.expr.accept(self)
        if _is_truthy(expr):
            node.then_stmt.accept(self)
        elif node.else_stmt:
            node.else_stmt.accept(self)

    def visit(self, node: BreakStmt):
        raise BreakException()

    def visit(self, node: ContinueStmt):
        raise ContinueException()

    def visit(self, node: ReturnStmt):
        # Ojo: node.expr es opcional
        value = 0 if not node.expr else node.expr.accept(self)
        raise ReturnException(value)

    def visit(self, node: ExprStmt):
        node.expr.accept(self)

    # Expressions

    def visit(self, node: ConstExpr):
        return node.value

    def visit(self, node: BinaryOpExpr):
        left = node.left.accept(self)
        right = node.right.accept(self)

        if node.op == '+':
            (isinstance(left, str) and isinstance(right, str)
             ) or self._check_numeric_operands(node, left, right)
            return left + right

        elif node.op == '-':
            self._check_numeric_operands(node, left, right)
            return left - right

        elif node.op == '*':
            self._check_numeric_operands(node, left, right)
            return left * right

        elif node.op == '/':
            self._check_numeric_operands(node, left, right)
            if isinstance(left, int) and isinstance(right, int):
                return left // right

            return left / right

        elif node.op == '%':
            self._check_numeric_operands(node, left, right)
            return left % right

        elif node.op == '==':
            return left == right

        elif node.op == '!=':
            return left != right

        elif node.op == '<':
            self._check_numeric_operands(node, left, right)
            return left < right

        elif node.op == '>':
            self._check_numeric_operands(node, left, right)
            return left > right

        elif node.op == '<=':
            self._check_numeric_operands(node, left, right)
            return left <= right

        elif node.op == '>=':
            self._check_numeric_operands(node, left, right)
            return left >= right

        else:
            raise NotImplementedError(f"Mal operador {node.op}")

 

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
        self.env = self.env.parents

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
        if node.opr == "+":
            return left + right
        elif node.opr == "-":
            return left - right
        elif node.opr == "*":
            return left * right
        elif node.opr == "/":
            return left / right
        elif node.opr == "==":
            return left == right
        elif node.opr == "!=":
            return left != right
        elif node.opr == "<":
            return left < right
        elif node.opr == ">":
            return left > right
        elif node.opr == "<=":
            return left <= right
        elif node.opr == ">=":
            return left >= right
        else:
            raise NotImplementedError(f"Operador desconocido {node.opr}")

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
            return -value
        elif node.opr == "!":
            return not _is_truthy(value)
        else:
            raise NotImplementedError(
                f"Operador unario desconocido {node.opr}")

    def visit(self, node: CallExpr):
        func = self.env[node.func_name]
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

