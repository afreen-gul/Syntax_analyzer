# parser_module.py — W++ Compiler
# Clean single-error reporting — minimum exact errors like real compilers

from symbol_table import SymbolTable


class Parser:

    def __init__(self, tokens):
        self.tokens = [t for t in tokens if t[0] != 'ERROR']
        self.pos = 0
        self.errors = []
        self.symbol_table = SymbolTable()

    # =========================================================
    # HELPERS
    # =========================================================

    def current(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def peek(self, offset=1):
        idx = self.pos + offset
        if idx < len(self.tokens):
            return self.tokens[idx]
        return None

    def eat(self, expected_type=None):
        """Consume token silently — caller is responsible for error message."""
        token = self.current()
        if token is None:
            return None
        if expected_type and token[0] != expected_type:
            return None     # caller decides what message to show
        self.pos += 1
        return token

    def expect(self, expected_type, message):
        """Consume token or emit ONE specific human-friendly error."""
        token = self.current()
        if token is None:
            self.errors.append(message + " (unexpected end of file)")
            return None
        if token[0] != expected_type:
            self.errors.append(f"{message} at line {token[2]}, col {token[3]}")
            return None
        self.pos += 1
        return token

    def error(self, msg, token=None):
        if token:
            self.errors.append(f"{msg} at line {token[2]}, col {token[3]}")
        else:
            self.errors.append(msg)

    def skip_to(self, *stop_types):
        while self.current() and self.current()[0] not in stop_types:
            self.pos += 1

    def is_type_keyword(self, token):
        return (token and token[0] == 'KEYWORD'
                and token[1] in ('int', 'float', 'double', 'char',
                                 'void', 'string', 'bool'))

    # =========================================================
    # ENTRY POINT
    # =========================================================

    def parse(self):
        while self.current() is not None:
            try:
                self.parse_statement()
            except Exception as e:
                self.errors.append(str(e))
                self.skip_to('END', 'RBRACE', 'LBRACE')
                if self.current() and self.current()[0] == 'END':
                    self.pos += 1

    # =========================================================
    # STATEMENT DISPATCHER
    # =========================================================

    def parse_statement(self):
        tok = self.current()
        if tok is None:
            return

        if self.is_type_keyword(tok) and self.peek() and \
                self.peek()[0] == 'IDENTIFIER' and self.peek(2) and \
                self.peek(2)[0] == 'LPAREN':
            self.parse_function_def()

        elif self.is_type_keyword(tok):
            self.parse_var_declaration()

        elif tok[0] == 'KEYWORD' and tok[1] == 'if':
            self.parse_if()

        elif tok[0] == 'KEYWORD' and tok[1] == 'while':
            self.parse_while()

        elif tok[0] == 'KEYWORD' and tok[1] == 'for':
            self.parse_for()

        elif tok[0] == 'KEYWORD' and tok[1] == 'return':
            self.parse_return()

        elif tok[0] == 'KEYWORD' and tok[1] == 'print':
            self.parse_print()

        elif tok[0] == 'IDENTIFIER' and self.peek() and \
                self.peek()[0] == 'ASSIGN':
            self.parse_assignment()

        elif tok[0] == 'IDENTIFIER' and self.peek() and \
                self.peek()[0] in ('INCREMENT', 'DECREMENT'):
            self.pos += 2
            self.expect('END', "Missing ';'")

        elif tok[0] == 'LBRACE':
            self.parse_block()

        elif tok[0] == 'RBRACE':
            return

        elif tok[0] == 'END':
            self.pos += 1

        else:
            self.error(f"Unexpected token '{tok[1]}'", tok)
            self.pos += 1

    # =========================================================
    # FUNCTION DEFINITION
    # =========================================================

    def parse_function_def(self):
        self.eat('KEYWORD')                     # return type
        self.eat('IDENTIFIER')                  # function name
        self.eat('LPAREN')
        while self.current() and self.current()[0] != 'RPAREN':
            if self.is_type_keyword(self.current()):
                ptype = self.eat('KEYWORD')
                if self.current() and self.current()[0] != 'IDENTIFIER':
                    self.error(
                        f"Invalid parameter name '{self.current()[1]}'"
                        f" — identifiers cannot start with a number",
                        self.current()
                    )
                    self.skip_to('COMMA', 'RPAREN')
                else:
                    pname = self.eat('IDENTIFIER')
                    if pname:
                        self.symbol_table.add(
                            pname[1], ptype[1] if ptype else '?'
                        )
            elif self.current()[0] == 'COMMA':
                self.pos += 1
            else:
                self.pos += 1
        self.expect('RPAREN', "Missing ')' after function parameters")
        self.parse_block()

    # =========================================================
    # VARIABLE DECLARATION
    # =========================================================

    def parse_var_declaration(self):
        type_tok = self.eat('KEYWORD')
        dtype = type_tok[1] if type_tok else '?'

        # guard: name must be a valid identifier
        if self.current() and self.current()[0] != 'IDENTIFIER':
            self.error(
                f"Invalid variable name '{self.current()[1]}'"
                f" — identifiers cannot start with a number",
                self.current()
            )
            self.skip_to('END')
            self.eat('END')
            return

        while True:
            name_tok = self.eat('IDENTIFIER')
            if name_tok:
                self.symbol_table.add(name_tok[1], dtype)

            if self.current() and self.current()[0] == 'ASSIGN':
                self.pos += 1
                self.parse_expression()

            if self.current() and self.current()[0] == 'COMMA':
                self.pos += 1
                if self.current() and self.current()[0] != 'IDENTIFIER':
                    self.error(
                        f"Invalid variable name '{self.current()[1]}'"
                        f" — identifiers cannot start with a number",
                        self.current()
                    )
                    self.skip_to('END')
                    self.eat('END')
                    return
                continue
            break

        self.expect('END', "Missing ';' after variable declaration")

    # =========================================================
    # ASSIGNMENT
    # =========================================================

    def parse_assignment(self):
        self.eat('IDENTIFIER')
        self.eat('ASSIGN')
        self.parse_expression()
        self.expect('END', "Missing ';' after assignment")

    # =========================================================
    # IF / ELSE
    # =========================================================

    def parse_if(self):
        self.eat('KEYWORD')         # if
        self.expect('LPAREN', "Missing '(' after 'if'")
        self.parse_expression()
        self.expect('RPAREN', "Missing ')' after if condition")
        self.parse_block_or_statement()

        while self.current() and \
              self.current()[0] == 'KEYWORD' and \
              self.current()[1] == 'else':
            self.pos += 1
            if self.current() and \
               self.current()[0] == 'KEYWORD' and \
               self.current()[1] == 'if':
                self.parse_if()
            else:
                self.parse_block_or_statement()

    # =========================================================
    # WHILE
    # =========================================================

    def parse_while(self):
        self.eat('KEYWORD')
        self.expect('LPAREN', "Missing '(' after 'while'")
        self.parse_expression()
        self.expect('RPAREN', "Missing ')' after while condition")
        self.parse_block_or_statement()

    # =========================================================
    # FOR
    # =========================================================

    def parse_for(self):
        self.eat('KEYWORD')         # for
        self.expect('LPAREN', "Missing '(' after 'for'")

        if self.current() and self.current()[0] != 'END':
            if self.is_type_keyword(self.current()):
                type_tok = self.eat('KEYWORD')
                if self.current() and self.current()[0] != 'IDENTIFIER':
                    self.error(
                        f"Invalid variable name '{self.current()[1]}'"
                        f" — identifiers cannot start with a number",
                        self.current()
                    )
                    self.skip_to('END')
                else:
                    name_tok = self.eat('IDENTIFIER')
                    if name_tok:
                        self.symbol_table.add(
                            name_tok[1], type_tok[1] if type_tok else '?'
                        )
                    if self.current() and self.current()[0] == 'ASSIGN':
                        self.pos += 1
                        self.parse_expression()
            else:
                self.parse_expression()
        self.expect('END', "Missing ';' in for-loop initializer")

        if self.current() and self.current()[0] != 'END':
            self.parse_expression()
        self.expect('END', "Missing ';' in for-loop condition")

        if self.current() and self.current()[0] != 'RPAREN':
            if self.current()[0] == 'IDENTIFIER' and self.peek() and \
                    self.peek()[0] in ('INCREMENT', 'DECREMENT'):
                self.pos += 2
            elif self.current()[0] == 'IDENTIFIER' and self.peek() and \
                    self.peek()[0] == 'ASSIGN':
                self.pos += 2
                self.parse_expression()
            else:
                self.parse_expression()

        self.expect('RPAREN', "Missing ')' after for-loop update")
        self.parse_block_or_statement()

    # =========================================================
    # RETURN
    # =========================================================

    def parse_return(self):
        self.eat('KEYWORD')
        if self.current() and self.current()[0] != 'END':
            self.parse_expression()
        self.expect('END', "Missing ';' after return statement")

    # =========================================================
    # PRINT
    # =========================================================

    def parse_print(self):
        self.eat('KEYWORD')
        self.expect('LPAREN', "Missing '(' after 'print'")
        while self.current() and self.current()[0] != 'RPAREN':
            self.parse_expression()
            if self.current() and self.current()[0] == 'COMMA':
                self.pos += 1
        self.expect('RPAREN', "Missing ')' after print arguments")
        self.expect('END', "Missing ';' after print statement")

    # =========================================================
    # BLOCK  { statements... }
    # =========================================================

    def parse_block(self):
        self.expect('LBRACE', "Missing '{'")
        while self.current() and self.current()[0] != 'RBRACE':
            self.parse_statement()
        self.expect('RBRACE', "Missing closing '}'")

    def parse_block_or_statement(self):
        if self.current() and self.current()[0] == 'LBRACE':
            self.parse_block()
        else:
            self.parse_statement()

    # =========================================================
    # EXPRESSION
    # =========================================================

    def parse_expression(self):
        self.parse_unary()
        binary_ops = ('OP', 'REL_OP', 'LOGICAL_OP')
        while self.current() and self.current()[0] in binary_ops:
            self.pos += 1
            self.parse_unary()

    def parse_unary(self):
        tok = self.current()
        if tok is None:
            return
        if tok[0] == 'OP' and tok[1] == '-':
            self.pos += 1
            self.parse_primary()
        elif tok[0] == 'LOGICAL_OP' and tok[1] == '!':
            self.pos += 1
            self.parse_primary()
        else:
            self.parse_primary()

    def parse_primary(self):
        tok = self.current()
        if tok is None:
            return

        if tok[0] == 'NUMBER':
            self.pos += 1

        elif tok[0] == 'STRING_LITERAL':
            self.pos += 1

        elif tok[0] == 'CHAR_LITERAL':
            self.pos += 1

        elif tok[0] == 'KEYWORD' and tok[1] in ('true', 'false'):
            self.pos += 1

        elif tok[0] == 'IDENTIFIER':
            self.pos += 1
            if self.current() and self.current()[0] == 'LPAREN':
                self.pos += 1
                while self.current() and self.current()[0] != 'RPAREN':
                    self.parse_expression()
                    if self.current() and self.current()[0] == 'COMMA':
                        self.pos += 1
                self.expect('RPAREN', "Missing ')' after function call arguments")
            elif self.current() and self.current()[0] in ('INCREMENT', 'DECREMENT'):
                self.pos += 1

        elif tok[0] == 'LPAREN':
            self.pos += 1
            self.parse_expression()
            self.expect('RPAREN', "Missing ')' in expression")

        else:
            self.error(f"Unexpected token '{tok[1]}' in expression", tok)
            self.pos += 1