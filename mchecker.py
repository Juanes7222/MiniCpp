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
from collections import ChainMap  # Tabla de Simbolos
from typing      import Union
from mccast       import *

class CheckError(Exception):
  pass


def _check_name(name, env:ChainMap):
  for n, e in enumerate(env.maps):
    if name in e:
      if not e[name]:
        raise CheckError("No se puede hacer referencia a una variable en su propia inicialización")
      else:
        return n
  raise CheckError(f"'{name}' no esta definido")


class Checker(Visitor):

  @classmethod
  def check(cls, n:Node, env:ChainMap, interp):
    checker = cls()
    n.accept(checker, env.new_child())
    return checker

  def check_type_compatibility(left_type, right_type):
    if left_type == right_type:
        return True
    if left_type == 'int' and right_type == 'float':
        return True  # Ensanchamiento implícito
    if left_type == 'float' and right_type == 'int':
        return True  # Ensanchamiento explícito con cast
    return False

  # Declarations


  def visit(self, n:Program, env:ChainMap):
    '''
    1. Crear una nueva tabla de simbolos
    2. Insertar dentro de esa tabla funciones como: scanf, printf
    3. Visitar todas las declaraciones
    '''
    env = ChainMap()
    env['scanf'] = True
    env['prinf'] = True

    main_found = False

    for decl in n.stmts:
        if isinstance(decl, FunctDeclStmt) and decl.name == 'main':
            main_found = True
        decl.accept(self, env)

    if not main_found:
        raise CheckError("La función 'main' no está definida")

  def visit(self, n:FunctDeclStmt, env:ChainMap):
    '''
    1. Guardar la función en la TS
    2. Crear una TS para la función
    3. Agregar n.params dentro de la TS
    4. Visitar n.stmts 
    '''
    env[n.ident] = n
    env = env.new_child()
    env['fun'] = True
    for p in n.params:
      env[p] = len(env)
    n.stmts.accept(self, env)

  def visit(self, n:VarDeclStmt, env:ChainMap, interp):
    '''
    1. Agregar n.ident a la TS actual
    '''
    env[n.ident] = n

  # Statements

  def visit(self, n:CompoundStmt, env: ChainMap, interp):
    '''
    1. Crear una tabla de simbolos
    2. Visitar Declaration/Statement
    '''
    newenv = env.new_child()
    for decl in n.decls:
      decl.accept(self, newenv, interp)
    for stmt in n.stmts:
      stmt.accept(self, newenv, interp)

  def visit(self, n:IfStmt, env:ChainMap, interp):

    '''
    1. Visitar n.expr (validar tipos)
    2. Visitar Stament por n.then
    3. Si existe opcion n.else_, visitar
    '''
    n.expr.accept(self, env, interp)
    n.then.accept(self, env, interp)
    if n.else_:
      n.else_.accept(self, env, interp)

  def visit(self, n: WhileStmt, env: ChainMap, interp):
    """
    1. Crear un nuevo entorno local para el ciclo `while`.
    2. Marcar que estamos dentro de un ciclo.
    3. Validar la condición del ciclo.
    4. Validar el cuerpo del ciclo.
    5. Al salir del ciclo, quitar la marca de ciclo.
    """
    # Crear un nuevo entorno local para el ciclo
    new_env = env.new_child()

    # Marcar el ciclo, acumulando el nivel de anidación
    new_env['cycle'] = new_env.get('cycle', 0) + 1

    # Validar que la condición del ciclo sea booleana
    cond_type = n.condition.accept(self, new_env, interp)
    if cond_type != 'bool':
        raise CheckError(f"La condición en el while debe ser de tipo booleano")

    # Validar el cuerpo del ciclo
    n.body.accept(self, new_env, interp)

    # Eliminar la marca del ciclo al salir
    new_env['cycle'] -= 1
    if new_env['cycle'] == 0:
        del new_env['cycle']


  def visit(self, n: ForStmt, env: ChainMap, interp):
    """
    1. Crear un nuevo entorno local para el ciclo `for`.
    2. Marcar que estamos dentro de un ciclo.
    3. Validar las partes del `for` (inicialización, condición, paso).
    4. Validar el cuerpo del ciclo.
    5. Al salir del ciclo, quitar la marca de ciclo.
    """
    # Crear un nuevo entorno local para el ciclo
    new_env = env.new_child()

    # Marcar el ciclo, acumulando el nivel de anidación
    new_env['cycle'] = new_env.get('cycle', 0) + 1

    # Validar la inicialización del for (puede ser una declaración o una expresión)
    n.for_init_stament.accept(self, new_env, interp)

    # Validar que la condición del ciclo sea booleana
    cond_type = n.condition.accept(self, new_env, interp)
    if cond_type != 'bool':
        raise CheckError(f"La condición en el for debe ser de tipo booleano")

    # Validar el paso del ciclo (expresión de incremento)
    n.step.accept(self, new_env, interp)

    # Validar el cuerpo del ciclo
    n.body.accept(self, new_env, interp)

    # Eliminar la marca del ciclo al salir
    new_env['cycle'] -= 1
    if new_env['cycle'] == 0:
        del new_env['cycle']


  def visit(self, n: Union[BreakStmt, ContinueStmt], env: ChainMap, interp):
    """
    1. Verificar que la instrucción break o continue esté dentro de un ciclo.
    2. Validar si hay ciclos anidados (múltiples niveles de ciclos).
    """
    # Nombre de la instrucción ('break' o 'continue')
    stmt_name = 'break' if isinstance(n, BreakStmt) else 'continue'

    # Verificar si estamos dentro de un ciclo
    if 'cycle' not in env or env['cycle'] <= 0:
        raise CheckError(f"Instrucción '{stmt_name}' fuera de un ciclo válido")

    # Si estamos dentro de un ciclo, la instrucción es válida

  def visit(self, node: ExprStmt, env: ChainMap, interp):
    node.expr.accept(self, env, interp)

  # Expressions

  def visit(self, n: ConstExpr, env: ChainMap, interp):
    """
    1. Devuelve el tipo de la constante.
    """
    if isinstance(n.value, bool):
        return 'bool'
    elif isinstance(n.value, int):
        return 'int'
    elif isinstance(n.value, float):
        return 'float'
    elif isinstance(n.value, str):
        return 'string'
    else:
        raise CheckError("Constante desconocida")

  def visit(self, n: CompoundStmt, env: ChainMap, interp):
    """
    1. Crear una nueva tabla de símbolos (entorno local).
    2. Procesar las declaraciones de variables en `local_decls`.
    3. Validar las instrucciones en `stmt_list`.
    """
    # Crear un nuevo entorno para el bloque
    new_env = env.new_child()

    # Procesar las declaraciones locales (variables)
    for decl in n.local_decls:
        decl.accept(self, new_env, interp)

    # Procesar las instrucciones
    for stmt in n.stmt_list:
        stmt.accept(self, new_env, interp)
        
  def visit(self, n: ArrayLoockupExpr, env: ChainMap, interp):
      """
      1. Verificar que el identificador `ident` sea un arreglo declarado.
      2. Validar que el índice sea de tipo entero.
      3. Retornar el tipo de los elementos del arreglo.
      """
      # Verificar que el arreglo esté definido
      if n.ident not in env:
          raise CheckError(f"Arreglo '{n.ident}' no está definido")
      
      # Obtener el tipo del identificador
      array_type = env[n.ident]
      if not array_type.startswith('array'):
          raise CheckError(f"'{n.ident}' no es un arreglo")

      # Verificar el índice (debe ser de tipo entero)
      index_type = n.index.accept(self, env, interp)
      if index_type != 'int':
          raise CheckError(f"El índice del arreglo '{n.ident}' debe ser de tipo entero, pero es '{index_type}'")
      
      # Retornar el tipo de los elementos del arreglo (por ejemplo, 'int', 'float', etc.)
      # Suponemos que array_type tiene el formato 'array<tipo>', por lo que extraemos el tipo.
      element_type = array_type[6:-1]  # Por ejemplo, 'array<int>' -> 'int'
      return element_type

  def visit(self, n: NewArrayExpr, env: ChainMap, interp):
    """
    1. Verificar que el identificador `ident` no esté ya definido en el mismo entorno.
    2. Validar que `size_expr` sea de tipo entero.
    3. Validar que `value` (si no es NullStmt) sea compatible con `array_type`.
    """
    # Verificar que el identificador no esté definido
    if n.ident in env:
        raise CheckError(f"El arreglo '{n.ident}' ya está definido en este entorno")

    # Validar que el tamaño del arreglo sea entero
    size_type = n.size_expr.accept(self, env, interp)
    if size_type != 'int':
        raise CheckError(f"El tamaño del arreglo '{n.ident}' debe ser de tipo entero")

    # Agregar el arreglo a la tabla de símbolos como 'array<tipo>'
    env[n.ident] = f'array<{n.array_type}>'

    # Validar el valor inicial, si no es una declaración vacía
    if not isinstance(n.value, NullStmt):
        value_type = n.value.accept(self, env, interp)
        if value_type != n.array_type:
            raise CheckError(f"El valor inicial del arreglo '{n.ident}' no es compatible con el tipo '{n.array_type}'")

  def visit(self, n: ArraySizeExpr, env: ChainMap, interp):
    """
    1. Verificar que el arreglo `array` esté definido.
    2. Validar que el identificador sea un arreglo.
    """
    if n.array not in env:
        raise CheckError(f"El arreglo '{n.array}' no está definido")

    # Verificar que el identificador sea un arreglo
    array_type = env[n.array]
    if not array_type.startswith('array'):
        raise CheckError(f"'{n.array}' no es un arreglo")

    # El resultado de ArraySizeExpr es siempre un entero (tamaño del arreglo)
    return 'int'

  def visit(self, n: ElseStmt, env: ChainMap, interp):
    """
    1. Visitar el cuerpo del bloque else.
    """
    # El cuerpo de un else es simplemente un bloque de instrucciones
    n.body.accept(self, env, interp)


  def visit(self, n: BinaryOpExpr, env:ChainMap, interp):
    '''
    1. visitar n.left y luego n.right
    2. Verificar compatibilidad de tipos
    '''
    n.left.accept(self, env, interp)
    n.right.accept(self, env, interp)
    
    left_type = n.left.accept(self, env, interp)
    right_type = n.right.accept(self, env, interp)

    if not self.check_type_compatibility(left_type, right_type):
        interp.ctxt.error(n, f"Incompatibilidad de tipos: {left_type} y {right_type}")
    return left_type  # O el tipo resultante de la operación

  def visit(self, n:UnaryOpExpr, env:ChainMap, interp):
    '''
    1. visitar n.expr
    2. validar si es un operador unario valido
    '''
    n.expr.accept(self, env, interp)

  def visit(self, n:VarExpr, env:ChainMap, interp):
    '''
    1. Verificar si n.ident existe en TS y obtener el tipo
    '''
    try:
      interp.localmap[id(n)] = _check_name(n.name, env)
    except CheckError as err:
      interp.ctxt.error(n, str(err))

  def visit(self, n:VarAssignmentExpr, env:ChainMap, interp):
    '''
    1. Validar n.ident
    2. Visitar n.expr
    3. Verificar si son tipos compatibles
    '''
    n.expr.accept(self, env, interp)
    try:
      interp.localmap[id(n)] = _check_name(n.name, env)
    except CheckError as err:
      interp.ctxt.error(n, str(err))

  def visit(self, n: CallExpr, env: ChainMap, interp):
    """
    1. Verificar que la función `n.func_name` esté definida.
    2. Si es `scanf` o `printf`, validar los argumentos.
    3. Verificar el número y tipo de los argumentos según la cadena de formato.
    """
    # Verificar si la función está definida
    if n.func_name not in env:
        raise CheckError(f"Función '{n.func_name}' no está definida")
    
    # Validar printf
    if n.func_name == 'printf':
        self._validate_printf(n, env, interp)
        return 'void'  # printf retorna void
    
    # Validar scanf
    elif n.func_name == 'scanf':
        self._validate_scanf(n, env, interp)
        return 'void'  # scanf retorna void

    # Validación general para otras funciones
    for arg in n.args:
        arg.accept(self, env, interp)

  def _validate_printf(self, n: CallExpr, env: ChainMap, interp):
      """
      Validar la llamada a printf:
      1. El primer argumento debe ser una cadena de formato.
      2. Los argumentos restantes deben coincidir con los especificadores de formato.
      """
      if len(n.args) == 0:
          raise CheckError("printf necesita al menos una cadena de formato")

      # El primer argumento debe ser una cadena de formato
      if not isinstance(n.args[0], ConstExpr) or not isinstance(n.args[0].value, str):
          raise CheckError("El primer argumento de printf debe ser una cadena de formato")

      format_string = n.args[0].value
      expected_types = self._parse_format_string(format_string)

      if len(expected_types) != len(n.args) - 1:
          raise CheckError(f"printf espera {len(expected_types)} argumentos, pero se dieron {len(n.args) - 1}")

      # Validar cada argumento según los especificadores de la cadena de formato
      for i, expected_type in enumerate(expected_types, start=1):
          arg_type = n.args[i].accept(self, env, interp)
          if arg_type != expected_type:
              raise CheckError(f"Argumento {i} de printf debe ser de tipo {expected_type}, pero se encontró {arg_type}")

  def _validate_scanf(self, n: CallExpr, env: ChainMap, interp):
      """
      Validar la llamada a scanf:
      1. El primer argumento debe ser una cadena de formato.
      2. Los argumentos restantes deben ser variables modificables y coincidir con los especificadores de formato.
      """
      if len(n.args) == 0:
          raise CheckError("scanf necesita al menos una cadena de formato")

      # El primer argumento debe ser una cadena de formato
      if not isinstance(n.args[0], ConstExpr) or not isinstance(n.args[0].value, str):
          raise CheckError("El primer argumento de scanf debe ser una cadena de formato")

      format_string = n.args[0].value
      expected_types = self._parse_format_string(format_string)

      if len(expected_types) != len(n.args) - 1:
          raise CheckError(f"scanf espera {len(expected_types)} argumentos, pero se dieron {len(n.args) - 1}")

      # Validar cada argumento según los especificadores de la cadena de formato
      for i, expected_type in enumerate(expected_types, start=1):
          if not isinstance(n.args[i], VarExpr):
              raise CheckError(f"Argumento {i} de scanf debe ser una variable modificable")
          arg_type = n.args[i].accept(self, env, interp)
          if arg_type != expected_type:
              raise CheckError(f"Argumento {i} de scanf debe ser de tipo {expected_type}, pero se encontró {arg_type}")

  def _parse_format_string(self, format_string):
      """
      Extrae los tipos esperados de la cadena de formato (por ejemplo, %d, %f, %s) y los convierte en tipos correspondientes.
      """
      import re
      type_map = {
          '%d': 'int',
          '%f': 'float',
          '%s': 'string',
          '%c': "char"
          # Agrega otros especificadores de formato según sea necesario
      }

      # Usar una expresión regular para encontrar todos los especificadores de formato en la cadena
      matches = re.findall(r'%[dfs]', format_string)
      return [type_map[m] for m in matches]


