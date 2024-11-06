# checker.py
'''
Analisis Semantico
------------------

En esta etapa del compilador debemos hacer lo siguiente:

1. Construir la tabla de Símbolos (puede usar ChainMap).
2. Validar que todo Identificador debe ser declarado previamente.
3. Agregar una instrucción de cast.
4. Validar que cualquier expresión debe tener compatibilidad de tipos.
5. Validar que exista una función main (puerta de entrada).
6. Implementar la función scanf.
7. Implementar la instrucción FOR.
8. Validar que las instrucciones BREAK y CONTINUE estén utilizada dentro de instrucciones WHILE/FOR.
'''
import re

from collections import ChainMap  # Tabla de Simbolos
from typing import Union
from mccast import *
from mctypesys import check_unary_op, check_binary_op


class CheckError(Exception):
    pass


def _check_name(name, env: ChainMap):
    for n, e in enumerate(env.maps):
        if name in e:
            if not e[name]:
                raise CheckError(
                    "No se puede hacer referencia a una variable en su propia inicialización")
            else:
                return n
    raise CheckError(f"'{name}' no esta definido")


class Checker(Visitor):

    @classmethod
    def check(cls, n: Node, env: ChainMap, interp):
        checker = cls()
        env = n.accept(checker, env, interp)
        return env

    def check_type_compatibility(self, left_type, right_type):
        if left_type == right_type:
            return True
        if left_type == 'int' and right_type == 'float':
            return True  # Ensanchamiento implícito
        if left_type == 'float' and right_type == 'int':
            return True  # Ensanchamiento explícito con cast
        return False
    
    def _validate_printf(self, n: CallExpr, env: ChainMap, interp):

        if len(n.args) == 0:
            raise CheckError("printf necesita al menos una cadena de formato")

        if not isinstance(n.args[0], ConstExpr) or not isinstance(n.args[0].value, str):
            raise CheckError(
                "El primer argumento de printf debe ser una cadena de formato")

        format_string = n.args[0].value
        expected_types = self._parse_format_string(format_string)

        if len(expected_types) != len(n.args) - 1:
            raise CheckError(f"printf espera {len(
                expected_types)} argumentos, pero se dieron {len(n.args) - 1}")

        for i, expected_type in enumerate(expected_types, start=1):
            arg_type = n.args[i].accept(self, env, interp)
            if arg_type != expected_type:
                raise CheckError(f"Argumento {i} de printf debe ser de tipo {expected_type}, pero se encontró {arg_type}")

    def _validate_scanf(self, n: CallExpr, env: ChainMap, interp):
        if len(n.args) == 0:
            raise CheckError("scanf necesita al menos una cadena de formato")

        if not isinstance(n.args[0], ConstExpr) or not isinstance(n.args[0].value, str):
            raise CheckError(
                "El primer argumento de scanf debe ser una cadena de formato")

        format_string = n.args[0].value
        expected_types = self._parse_format_string(format_string)

        if len(expected_types) != len(n.args) - 1:
            raise CheckError(f"scanf espera {len(
                expected_types)} argumentos, pero se dieron {len(n.args) - 1}")

        for i, expected_type in enumerate(expected_types, start=1):
            if not isinstance(n.args[i], VarExpr):
                raise CheckError(
                    f"Argumento {i} de scanf debe ser una variable modificable")
            arg_type = n.args[i].accept(self, env, interp)
            if arg_type != expected_type:
                raise CheckError(f"Argumento {i} de scanf debe ser de tipo {expected_type}, pero se encontró {arg_type}")

    def _parse_format_string(self, format_string):
        type_map = {
            '%d': 'int',
            '%f': 'float',
            '%F': 'float',
            '%e': 'float',
            '%E': 'float',
            '%a': 'float',
            '%A': 'float',
            '%g': 'float',
            '%G': 'float',
            '%s': 'string',
            '%c': "char",
            '%o': 'int',
            '%x': 'int',
            '%X': 'int',
            '%u': 'int',
        }

        matches = re.findall(r'%[dfs]', format_string)
        return [type_map[m] for m in matches]

    # Declarations

    def visit(self, n: Program, env: ChainMap, interp):

        main_found = False

        for decl in n.stmts:
            if isinstance(decl, FunctDeclStmt) and decl.ident == 'main':
                main_found = True
            decl.accept(self, env, interp)

        if not main_found:
            raise CheckError("La función 'main' no está definida")
        
        return env

    def visit(self, n: FunctDeclStmt, env: ChainMap, interp):
        env[n.ident] = n
        env = env.new_child()
        env['fun'] = n.type_
        for p in n.params:
            env[p.ident] = p
        n.body.accept(self, env, interp)

    def visit(self, n: VarDeclStmt, env: ChainMap, interp):
        env[n.ident] = n

    # Statements

    def visit(self, n: StaticVarDeclStmt, env: ChainMap, interp):

        if n.ident in env:
            raise CheckError(f"Variable estática '{n.ident}' ya está definida en este entorno")

        env[n.ident] = n

    def visit(self, n: CompoundStmt, env: ChainMap, interp):

        newenv = env.new_child()
        for decl in n.decls:
            decl.accept(self, newenv, interp)
        for stmt in n.stmts:
                stmt.accept(self, newenv, interp)

    def visit(self, n: ReturnStmt, env: ChainMap, interp):
        """
        1. Si la función tiene un tipo de retorno, validar que el tipo de `expr` coincida.
        2. Si no tiene un valor de retorno (void), validar que `expr` sea None.
        """
        if 'fun' not in env:
            raise CheckError("Instrucción return usada fuera de una función")

        func_type = env['fun']

        if func_type != 'void':
            if n.expr is None:
                raise CheckError(f"Se esperaba un valor de retorno de tipo '{func_type}', pero no se encontró ningún valor.")
            return_type = n.expr.accept(self, env, interp)
            if return_type != func_type:
                raise CheckError(f"El valor de retorno es de tipo '{return_type}', pero se esperaba '{func_type}'")
        
        elif func_type == 'void' and n.expr is not None:
            raise CheckError("La función de tipo void no debe devolver un valor")


    def visit(self, n: IfStmt, env: ChainMap, interp):

        n.condition.accept(self, env, interp)
        n.then_brach.accept(self, env, interp)
        if n.else_branch:
            n.else_branch.accept(self, env, interp)

    def visit(self, n: WhileStmt, env: ChainMap, interp):
        new_env = env.new_child()

        new_env['cycle'] = new_env.get('cycle', 0) + 1

        cond_type = n.condition.accept(self, new_env, interp)
        if cond_type != 'bool':
            raise CheckError(
                f"La condición en el while debe ser de tipo booleano")

        n.body.accept(self, new_env, interp)

        new_env['cycle'] -= 1
        if new_env['cycle'] == 0:
            del new_env['cycle']

    def visit(self, n: ForStmt, env: ChainMap, interp):
        new_env = env.new_child()

        new_env['cycle'] = new_env.get('cycle', 0) + 1

        n.for_init_stament.accept(self, new_env, interp)

        cond_type = n.condition.accept(self, new_env, interp)
        if cond_type != 'bool':
            raise CheckError(
                f"La condición en el for debe ser de tipo booleano")

        n.step.accept(self, new_env, interp)

        n.body.accept(self, new_env, interp)

        new_env['cycle'] -= 1
        if new_env['cycle'] == 0:
            del new_env['cycle']

    def visit(self, n: Union[BreakStmt, ContinueStmt], env: ChainMap, interp):
        stmt_name = 'break' if isinstance(n, BreakStmt) else 'continue'

        if 'cycle' not in env or env['cycle'] <= 0:
            raise CheckError(
                f"Instrucción '{stmt_name}' fuera de un ciclo válido")

    def visit(self, node: ExprStmt, env: ChainMap, interp):
        node.expr.accept(self, env, interp)

    # Expressions

    def visit(self, n: ConstExpr, env: ChainMap, interp):
        if isinstance(n.value, bool):
            return 'bool'
        elif isinstance(n.value, int):
            return 'int'
        elif isinstance(n.value, float):
            return 'float'
        elif isinstance(n.value, str):
            return 'string'
        elif n.value is None:
            return "null"
        else:
            raise CheckError("Constante desconocida")

    def visit(self, n: ArrayLoockupExpr, env: ChainMap, interp):
        if n.ident not in env:
            raise CheckError(f"Arreglo '{n.ident}' no está definido")

        array_type = env[n.ident]
        if not array_type.startswith('array'):
            raise CheckError(f"'{n.ident}' no es un arreglo")

        index_type = n.index.accept(self, env, interp)
        if index_type != 'int':
            raise CheckError(f"El índice del arreglo '{n.ident}' debe ser de tipo entero, pero es '{index_type}'")

        element_type = array_type[6:-1]  # Por ejemplo, 'array<int>' -> 'int'
        return element_type

    def visit(self, n: NewArrayExpr, env: ChainMap, interp):
        if n.ident in env:
            raise CheckError(
                f"El arreglo '{n.ident}' ya está definido en este entorno")

        size_type = n.size_expr.accept(self, env, interp)
        if size_type != 'int':
            raise CheckError(f"El tamaño del arreglo '{n.ident}' debe ser de tipo entero")
        
        if not isinstance(n.value, NullStmt):
            if len(n.value) != n.size_expr.value:
                raise CheckError(f"El tamaño del arreglo '{n.ident}' debe ser de {n.size_expr.value}")

        env[n.ident] = n

        if not isinstance(n.value, NullStmt):
            value_type = {val.accept(self, env, interp) for val in n.value}
            if len(value_type) != 1:
                raise CheckError(f"El valor inicial del arreglo '{n.ident}' no es compatible con el tipo '{n.type_}'")
            value_type = list(value_type)[0]
            if value_type != n.type_:
                raise CheckError(f"El valor inicial del arreglo '{n.ident}' no es compatible con el tipo '{n.type_}'")

    def visit(self, n: ArraySizeExpr, env: ChainMap, interp):
        if n.array not in env:
            raise CheckError(f"El arreglo '{n.array}' no está definido")

        array_type = env[n.array]
        if not array_type.startswith('array'):
            raise CheckError(f"'{n.array}' no es un arreglo")

        return 'int'

    def visit(self, n: ElseStmt, env: ChainMap, interp):
        n.body.accept(self, env, interp)

    def visit(self, n: BinaryOpExpr, env: ChainMap, interp):
        left_type = n.left.accept(self, env, interp)
        right_type = n.right.accept(self, env, interp)

        result_type = check_binary_op(n.opr, left_type, right_type)
        
        if result_type is None:
            interp.ctxt.error(n, f"Incompatibilidad de tipos en operación binaria: {left_type} {n.opr} {right_type}")
            return None

        return result_type

    def visit(self, n: UnaryOpExpr, env: ChainMap, interp):
        expr_type = n.expr.accept(self, env, interp)
        
         # Verificar que el operador se aplique a variables de tipo int o float
        if n.opr in ('++', '--') and expr_type not in ('int', 'float'):
            raise CheckError(
                f"El operador '{n.opr}' solo se puede aplicar a tipos numéricos (int o float), encontrado: '{expr_type}'"
            )

        result_type = check_unary_op(n.opr, expr_type)
        
        if result_type is None:
            interp.ctxt.error(n, f"Incompatibilidad de tipos en operación unaria: {n.opr} {expr_type}")
            return None

        return result_type
    
    def visit(self, n: VarExpr, env: ChainMap, interp):
        try:
            interp.localmap[id(n)] = _check_name(n.ident, env)
            return env[n.ident].type_
        except CheckError as err:
            interp.ctxt.error(n, str(err))

    def visit(self, n: VarAssignmentExpr, env: ChainMap, interp):
        n.expr.accept(self, env, interp)
        try:
            interp.localmap[id(n)] = _check_name(n.ident, env)
            return env[n.ident].type_
        except CheckError as err:
            interp.ctxt.error(n, str(err))
            
    def visit(self, n: CompoundAssignmentExpr, env: ChainMap, interp):
        # Verificar que la variable esté definida
        var_type = n.ident.accept(self, env, interp)
        
        # Verificar el tipo de la expresión del lado derecho
        expr_type = n.expr.accept(self, env, interp)

        # Validar la operación usando la función `check_binary_op` para tipos compatibles
        result_type = check_binary_op(n.opr, var_type, expr_type)
        if result_type is None:
            raise CheckError(
                f"Incompatibilidad de tipos: '{var_type}' no es compatible con '{expr_type}' para la operación '{n.opr}'"
            )
        return result_type

    def visit(self, n: CallExpr, env: ChainMap, interp):
        if n.func_name not in env:
            raise CheckError(f"Función '{n.func_name}' no está definida")

        if n.func_name == 'printf':
            self._validate_printf(n, env, interp)
            return 'void'  # printf retorna void

        elif n.func_name == 'scanf':
            self._validate_scanf(n, env, interp)
            return 'void'  # scanf retorna void

        for arg in n.args:
            arg.accept(self, env, interp)

