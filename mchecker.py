
from collections import ChainMap  # Tabla de Simbolos
from typing import Union
from mccast import *
from mctypesys import check_unary_op, check_binary_op, loockup_type, _parse_format_string
from mctypes import *


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
        expected_types = _parse_format_string(format_string)

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
        expected_types = _parse_format_string(format_string)

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
    
    def _check_property(self, class_: ClassDeclStmt, property_name):
        # Verificar que la propiedad existe en la clase
        for property in class_.properties:
            if property_name == property.ident:
                return property      
        raise CheckError(f"La propiedad '{property_name}' no está definida en la clase '{class_.ident}'")
    
    def _check_method(self, class_: ClassDeclStmt, method_name):
        
        for method in class_.methods:
            if method_name == method.ident:
                return method
        raise CheckError(f"El metodo '{method_name}' no está definida en la clase '{class_.ident}'")
        

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
            if len(n.value) == 1:
                return 'char'
            return 'string'
        elif n.value is None:
            return "null"
        else:
            raise CheckError("Constante desconocida")

    def visit(self, n: ArrayLoockupExpr, env: ChainMap, interp):
        if n.ident not in env:
            raise CheckError(f"Arreglo '{n.ident}' no está definido")

        array_type = env[n.ident]

        index_type = n.index.accept(self, env, interp)
        if index_type != 'int':
            raise CheckError(f"El índice del arreglo '{n.ident}' debe ser de tipo entero, pero es '{index_type}'")

        element_type = array_type.type_  # Por ejemplo, 'array<int>' -> 'int'
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
            
    def visit(self, n: ArrayAssignmentExpr, env: ChainMap, interp):
        """
        Valida la asignación a un elemento de un arreglo.
        """
        # Verificar que el arreglo existe
        if n.array not in env:
            raise CheckError(f"El arreglo '{n.array}' no está definido")

        # Verificar que es un arreglo
        array_info = env[n.array]
        if not isinstance(array_info, NewArrayExpr):
            raise CheckError(f"'{n.array}' no es un arreglo válido")

        # Verificar el índice
        index_type = n.index.accept(self, env, interp)
        if index_type != 'int':
            raise CheckError(f"El índice del arreglo '{n.array}' debe ser de tipo entero, pero se encontró '{index_type}'")

        # Verificar el valor asignado
        value_type = n.expr.accept(self, env, interp)
        element_type = array_info.type_
        if not self.check_type_compatibility(element_type, value_type):
            raise CheckError(
                f"Incompatibilidad de tipos: no se puede asignar un valor de tipo '{value_type}' "
                f"a un elemento del arreglo '{n.array}' de tipo '{element_type}'"
            )


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
        """
        Maneja expresiones de asignación compuesta, como 'x += 5'.
        """
        # Verificar que la variable está definida
        if n.ident.ident not in env:
            raise CheckError(f"La variable '{n.ident}' no está definida")

        # Obtener el tipo de la variable
        var_type = env[n.ident.ident].type_
        if not var_type:
            raise CheckError(f"No se puede determinar el tipo de la variable '{n.ident.ident}'")

        # Evaluar la expresión a la derecha del operador compuesto
        right_type = n.expr.accept(self, env, interp)
        if not right_type:
            raise CheckError(f"No se puede determinar el tipo de la expresión en '{n.expr}'")

        # Validar la compatibilidad del operador y los tipos
        result_type = check_binary_op(n.opr[0], var_type, right_type)  # El operador compuesto usa la primera parte (e.g., '+' en '+=')
        if not result_type:
            raise CheckError(
                f"Incompatibilidad de tipos en '{n.ident} {n.opr} ...': "
                f"'{var_type}' y '{right_type}' no son compatibles"
            )

        # Actualizar el valor de la variable en el entorno
        var_value = env[n.ident.ident].expr.value
        if isinstance(n.expr, ConstExpr):
            expr_value = n.expr.value
        else:
            expr_value = env[n.expr.ident].expr.value
        new_value = eval(f"{var_value} {n.opr[0]} {expr_value}")  # Aplica la operación
        env[n.ident.ident] = VarDeclStmt(ident=n.ident.ident, type_=var_type, expr=ConstExpr(new_value))

        # Retorna el tipo resultante de la operación
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
            
        return env[n.func_name].type_
            
    def visit(self, n: ClassDeclStmt, env: ChainMap, interp):
        # Verificar si la clase ya está declarada
        if n.ident in env:
            raise CheckError(f"La clase '{n.ident}' ya está definida")

        # Resolver la clase base
        base_class = None
        if n.sclass:
            if n.sclass not in env:
                raise CheckError(f"La clase base '{n.sclass}' no está definida")
            base_class = env[n.sclass]  # Recuperar la instancia de la clase base

        # Crear el entorno de la clase
        class_env = env.new_child()
        class_env['this'] = n.ident
        class_env[n.ident] = n

        # Registrar las propiedades en el entorno de la clase
        for prop in n.properties:
            if prop.ident in class_env:
                raise CheckError(f"La propiedad '{prop.ident}' ya está definida en la clase '{n.ident}'")
            class_env[prop.ident] = prop
            prop.accept(self, class_env, interp)

        # Registrar los métodos en el entorno de la clase
        for method in n.methods:
            if method.ident in class_env:
                raise CheckError(f"El método '{method.ident}' ya está definido en la clase '{n.ident}'")
            class_env[method.ident] = method
            method.accept(self, class_env, interp)

        # Registrar la clase en el entorno global
        env[n.ident] = n
        
    def visit(self, n: ClassMethodDecl, env: ChainMap, interp):
        # Crear un entorno nuevo para los parámetros del método
        method_env = env.new_child()
        method_env["fun"] = n.type_

        # Registrar los parámetros en el entorno del método
        for param in n.params:
            if param.ident in method_env:
                raise CheckError(f"El parámetro '{param.ident}' ya está definido en el método '{n.name}'")
            method_env[param.ident] = param

        # Validar el cuerpo del método
        n.body.accept(self, method_env, interp)

    def visit(self, n: ClassPropertyDecl, env: ChainMap, interp):
        # Verificar si el tipo es válido
        if not loockup_type(n.type_):
            raise CheckError(f"Tipo desconocido '{n.type_}' para la propiedad '{n.name}'")

        # Verificar si el valor inicial es compatible con el tipo
        if n.value:
            value_type = n.value.accept(self, env, interp)
            if not self.check_type_compatibility(n.type_, value_type):
                raise CheckError(f"Incompatibilidad de tipos: '{n.type_}' y '{value_type}' en la inicialización de '{n.name}'")
            
    def visit(self, n: ClassArrayPropertyDecl, env: ChainMap, interp):
        type_size = n.size.accept(self, env, interp)
        if type_size != 'int':
            raise CheckError(f"Tamaño invalido para arreglo {n.ident}: int --> {type_size}")
        
        if len(n.values) > 0:
            if len(n.values) < n.size.value:
                raise CheckError(f"Tamaño invalido para arreglo {n.ident}: int --> {type_size}")
            
        for value in n.values:
            value_type = value.accept(self, env, interp)
            if value_type != n.type_:
                raise CheckError(f"Elemento invalido para arreglo {n.ident}: {n.type_} --> {value_type}")
        
        # Registrar el arreglo en el entorno
        env[n.ident] = n


    def visit(self, n: This, env: ChainMap, interp):
        # Verificar que estamos dentro del contexto de una clase
        if 'this' not in env:
            raise CheckError("Uso de 'this' fuera del contexto de una clase")
        return env['this']
    
    def visit(self, n: SuperAccess, env: ChainMap, interp):
        # Verificar que estamos dentro de una clase derivada
        if 'this' not in env:
            raise CheckError("Uso de 'super' fuera del contexto de una clase")
        
        class_instance = env['this']
        class_ = env[class_instance]
        base_class = env.get(class_.sclass)

        if not base_class:
            raise CheckError(f"La clase '{class_instance.ident}' no tiene clase base")

        # Verificar que el atributo existe en la clase base
        property = self._check_property(base_class, n.ident)

        return property.type_


    def visit(self, n: SuperMethodCall, env: ChainMap, interp):
        # Verificar que estamos dentro de una clase derivada
        if 'this' not in env:
            raise CheckError("Uso de 'super' fuera del contexto de una clase")
        
        class_instance = env['this']
        class_ = env[class_instance]
        base_class = env.get(class_.sclass)

        if not base_class:
            raise CheckError(f"La clase '{class_instance.ident}' no tiene clase base")

        method = self._check_method(base_class, n.ident)

        # Validar los argumentos del método
        if len(n.args) != len(method.params):
            raise CheckError(f"El método '{n.ident}' espera {len(method.params)} argumentos, pero se proporcionaron {len(n.args)}")
        
        for arg, param in zip(n.args, method.params):
            arg_type = arg.accept(self, env, interp)
            if not self.check_type_compatibility(param.type_, arg_type):
                raise CheckError(f"Incompatibilidad de tipos en los argumentos del método '{n.name}'")

        return method.type_

    def visit(self, n: ClassInstanceCreation, env: ChainMap, interp):
        # Verificar que la clase existe
        if n.type_ not in env:
            raise CheckError(f"La clase '{n.type_}' no está definida")

        # Verificar que el constructor existe
        class_type = env[n.type_]
        
        # Verificar que el nombre de la variable no esté definido en el entorno actual
        if n.ident in env.maps[0]:
            raise CheckError(f"El nombre '{n.ident}' ya está definido en este contexto")

        # Registrar la variable en el entorno
        env[n.ident] = n



    def visit(self, n: Get, env: ChainMap, interp):
        
        obj_name = n.obj.accept(self, env, interp)
        obj_type = env[obj_name]

        # Verificar que el objeto es una clase válida
        property = self._check_property(obj_type, n.ident)

        # Verificar el acceso a la propiedad
        property_access = property.access
        if property_access == 'private' and env.get('this') != obj_name:
            raise CheckError(f"Acceso privado a la propiedad '{n.ident}' no permitido")
        return property.type_
    
    def visit(self, n: Set, env: ChainMap, interp):
        obj_name = n.obj.accept(self, env, interp)
        obj_type = env[obj_name]
        # Verificar que el objeto es una clase válida

        property = self._check_property(obj_type, n.ident)
        # Verificar el acceso a la propiedad
        property_access = property.access
        if property_access == 'private' and env.get('this') != obj_name:
            raise CheckError(f"Acceso privado a la propiedad '{n.ident}' no permitido")

        # Verificar compatibilidad de tipos
        value_type = n.value.accept(self, env, interp)
        property_type = property.type_
        if not self.check_type_compatibility(property_type, value_type):
            raise CheckError(f"Incompatibilidad de tipos: '{property_type}' y '{value_type}' en la asignación a '{n.ident}'")

    def visit(self, n: CallMethod, env: ChainMap, interp):
        obj_name = n.obj.accept(self, env, interp)
        
        obj_type = env[obj_name]

        method = self._check_method(obj_type, n.ident)
        # Validar argumentos
        if len(n.args) != len(method.params):
            raise CheckError(f"El método '{n.ident}' espera {len(method.params)} argumentos, pero se proporcionaron {len(n.args)}")

        for i, (arg, param) in enumerate(zip(n.args, method.params)):
            arg_type = arg.accept(self, env, interp)
            if not self.check_type_compatibility(param.type_, arg_type):
                raise CheckError(f"Tipo incompatible en el argumento {i + 1} para el método '{n.ident}'")

        return method.type_
