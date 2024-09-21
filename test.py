import unittest
from mclex import Lexer

class TestLexer(unittest.TestCase):
    
    def setUp(self):
        self.lexer = Lexer()

    def test_reserved_words(self):
        data = 'void bool int float if else for while class return break continue new and or not private public protected'
        expected_tokens = [
            'VOID', 'BOOL', 'INT', 'FLOAT', 'IF', 'ELSE', 'FOR', 'WHILE', 'CLASS', 
            'RETURN', 'BREAK', 'CONTINUE', 'NEW', 'AND', 'OR', 'NOT', 'PRIVATE', 'PUBLIC', 'PROTECTED'
        ]
        tokens = [tok.type for tok in self.lexer.tokenize(data)]
        self.assertEqual(tokens, expected_tokens)

    def test_identifiers(self):
        data = 'variable1 _var2 AnotherVar'
        expected_tokens = ['IDENT', 'IDENT', 'IDENT']
        tokens = [tok.type for tok in self.lexer.tokenize(data)]
        self.assertEqual(tokens, expected_tokens)
    
    def test_numbers(self):
        data = '123 -456 78.90 0.001 -0.1'
        expected_tokens = ['INT_LIT', 'INT_LIT', 'FLOAT_LIT', 'FLOAT_LIT', 'FLOAT_LIT']
        tokens = [tok.type for tok in self.lexer.tokenize(data)]
        self.assertEqual(tokens, expected_tokens)
    
    def test_strings(self):
        data = '"Hello, World!" "String with \\"escaped quotes\\" and \\\\ backslashes"'
        expected_tokens = ['STRING', 'STRING']
        tokens = [tok.type for tok in self.lexer.tokenize(data)]
        self.assertEqual(tokens, expected_tokens)

    def test_operators_and_symbols(self):
        data = '+ - * / % = == != < > <= >= && || ! & | ~'
        expected_tokens = list(data.split())
        tokens = [tok.value for tok in self.lexer.tokenize(data)]
        self.assertEqual(tokens, expected_tokens)
    
    def test_single_line_comment(self):
        data = 'int a = 10; // This is a comment\n'
        expected_tokens = ['INT', 'IDENT', '=', 'INT_LIT', ';']
        tokens = [tok.type for tok in self.lexer.tokenize(data)]
        self.assertEqual(tokens, expected_tokens)
    
    def test_multi_line_comment(self):
        data = '''
        /* This is a 
           multi-line comment */
        float b = 0.5;
        '''
        expected_tokens = ['FLOAT', 'IDENT', '=', 'FLOAT_LIT', ';']
        tokens = [tok.type for tok in self.lexer.tokenize(data)]
        self.assertEqual(tokens, expected_tokens)

    def test_complex_comment(self):
        data = '''
        /****************************************
         * This is another comment              *
         ****************************************/
        return 0;
        '''
        expected_tokens = ['RETURN', 'INT_LIT', ';']
        tokens = [tok.type for tok in self.lexer.tokenize(data)]
        self.assertEqual(tokens, expected_tokens)
    
    def test_combined_input(self):
        data = '''
        void main(void) {
            printf("Hello, world!\n");
            int i = 42;
            float x = 0.3;
            /********************************
             * Block comment example *
             ********************************/
            if (i > 10) return i;
        }
        '''
        expected_tokens = [
            'VOID', 'IDENT', '(', 'VOID', ')', '{', 'IDENT', '(', 'STRING', ')', ';',
            'INT', 'IDENT', '=', 'INT_LIT', ';', 'FLOAT', 'IDENT', '=', 'FLOAT_LIT', ';',
            'IF', '(', 'IDENT', '>', 'INT_LIT', ')', 'RETURN', 'IDENT', ';', '}'
        ]
        tokens = [tok.type for tok in self.lexer.tokenize(data)]
        self.assertEqual(tokens, expected_tokens)

    def test_class_declaration(self):
        data = '''
        class MyClass {
            private:
                int secretVar;
            public:
                MyClass() {}
                void publicMethod() {
                    float x = 1.0;
                }
            protected:
                void protectedMethod() {}
        }
        '''
        expected_tokens = [
            'CLASS', 'IDENT', '{',
            'PRIVATE', ':', 'INT', 'IDENT', ';',
            'PUBLIC', ':', 'IDENT', '(', ')', '{', '}',
            'VOID', 'IDENT', '(', ')', '{',
            'FLOAT', 'IDENT', '=', 'FLOAT_LIT', ';', '}',
            'PROTECTED', ':', 'VOID', 'IDENT', '(', ')', '{', '}', 
            '}'
        ]
        tokens = [tok.type for tok in self.lexer.tokenize(data)]
        self.assertEqual(tokens, expected_tokens)

if __name__ == '__main__':
    unittest.main()