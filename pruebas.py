from contextlib import redirect_stdout
from rich       import print

from mclex      import print_lexer
from mcparser   import gen_ast
from mcontext   import Context

with open("./mandel.mcc", encoding='utf-8') as file:
      source = file.read()
context = Context()

context.parse(source)
context.run()