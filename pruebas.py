
from mcontext   import Context, print_symbol_table

with open("./hola.mcc", encoding='utf-8') as file:
      source = file.read()
context = Context()

context.parse(source)
context.run()