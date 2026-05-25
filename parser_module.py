# parser_module.py — W++ Compiler
# Flexible + crash-safe version (STRICT + FLEX support)

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
        tok = self.current()
        if tok is None:
            return None
        if expected_type and tok[0] != expected_type:
            return None
        self.pos += 1
        return tok

    def expect(self, expected_type, message):
        tok = self.current()
        if tok is None:
            self.errors.append(message + " (unexpected end of file)")
            return None
        if tok[0] != expected_type:
            self.errors.append(f"{message} at line {tok[2]}, col {tok[3]}")
            return None
        self.pos += 1
        return tok

    def error(self, msg, tok=None):
        if tok:
            self.errors.append(f"{msg} at line {tok[2]}, col {tok[3]}")
        else:
            self.errors.append(msg)

    def skip_to(self, *types):
        while self.current() and self.current()[0] not in types:
            self.pos += 1

    def _has_block_after_call(self):
        """Lookahead: after identifier ( ... ) is there a { ?"""
        i = self.pos + 1  # skip identifier, start at LPAREN
        if i >= len(self.tokens) or self.tokens[i][0] != 'LPAREN':
            return False
        depth = 0
        while i < len(self.tokens):
            t = self.tokens[i][0]
            if t == 'LPAREN':
                depth += 1
            elif t == 'RPAREN':
                depth -= 1
                if depth == 0:
                    i += 1
                    return i < len(self.tokens) and self.tokens[i][0] == 'LBRACE'
            i += 1
        return False

    def is_type_keyword(self, tok):
        return tok and tok[0] == 'KEYWORD' and tok[1] in (
            'int', 'float', 'double', 'char', 'void', 'string', 'bool'
        )

    # =========================================================
    # ENTRY
    # =========================================================

    def parse(self):
        while self.current():
            try:
                self.parse_statement()
            except Exception:
                self.skip_to('END', 'RBRACE', 'LBRACE')
                if self.current() and self.current()[0] in ('END', 'RBRACE'):
                    self.pos += 1

    # =========================================================
    # STATEMENTS
    # =========================================================

    def parse_statement(self):
        tok = self.current()
        if not tok:
            return

        # ---------------- FUNCTION ----------------
        # type identifier ( ...  → function def  e.g.  int main() { }
        if (self.is_type_keyword(tok)
                and self.peek(1)
                and self.peek(1)[0] == 'IDENTIFIER'
                and self.peek(2)
                and self.peek(2)[0] == 'LPAREN'):
            self.parse_function_def()

        # identifier ( ...  → function def without return type  e.g.  main() { }
        elif (tok[0] == 'IDENTIFIER'
                and self.peek(1)
                and self.peek(1)[0] == 'LPAREN'
                and self.peek(2)
                and self.peek(2)[0] in ('RPAREN', 'KEYWORD', 'IDENTIFIER')):
            self.parse_function_def_no_type()

        # ---------------- VARIABLES ----------------
        elif self.is_type_keyword(tok):
            self.parse_var_declaration()

        # ---------------- CONTROL ----------------
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

        # ---------------- BEGIN / END SUPPORT ----------------
        elif tok[0] == 'KEYWORD' and tok[1] == 'begin':
            self.pos += 1
            self.parse_begin_block()

        elif tok[0] == 'KEYWORD' and tok[1] == 'end':
            self.pos += 1
            return

        # ---------------- ASSIGNMENT / CALL ----------------
        elif tok[0] == 'IDENTIFIER' and self.peek() and self.peek()[0] == 'ASSIGN':
            self.parse_assignment()

        elif tok[0] == 'IDENTIFIER' and self.peek() and self.peek()[0] in ('INCREMENT', 'DECREMENT'):
            self.pos += 2
            self.expect('END', "Missing ';'")

        # named block:  Identifier { ... }
        elif (tok[0] == 'IDENTIFIER'
                and self.peek(1)
                and self.peek(1)[0] == 'LBRACE'):
            self.pos += 1   # eat identifier
            self.parse_block()

        # named block with args:  Identifier("x") { ... }
        elif (tok[0] == 'IDENTIFIER'
                and self.peek(1)
                and self.peek(1)[0] == 'LPAREN'
                and self._has_block_after_call()):
            self.pos += 1   # eat identifier
            self.eat('LPAREN')
            while self.current() and self.current()[0] != 'RPAREN':
                self.parse_expression()
                if self.current() and self.current()[0] == 'COMMA':
                    self.pos += 1
            self.expect('RPAREN', "Missing ')'")
            self.parse_block()

        # standalone function call:  foo(...)  ;
        elif tok[0] == 'IDENTIFIER' and self.peek() and self.peek()[0] == 'LPAREN':
            self.parse_expression()
            self.expect('END', "Missing ';'")

        # [ ] wrapper — skip gracefully (e.g. [Character(...){...}])
        elif tok[0] == 'LBRACKET':
            self.pos += 1
            while self.current() and self.current()[0] != 'RBRACKET':
                self.parse_statement()
            if self.current() and self.current()[0] == 'RBRACKET':
                self.pos += 1

        # ---------------- BLOCK ----------------
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
    # BEGIN BLOCK (FLEX SUPPORT)
    # =========================================================

    def parse_begin_block(self):
        while self.current() and not (
            self.current()[0] == 'KEYWORD' and self.current()[1] == 'end'
        ):
            self.parse_statement()

    # =========================================================
    # FUNCTION
    # =========================================================

    def parse_function_def_no_type(self):
        """Handle functions without explicit return type: main() { }"""
        self.eat('IDENTIFIER')    # function name
        self.eat('LPAREN')

        while self.current() and self.current()[0] != 'RPAREN':
            if self.is_type_keyword(self.current()):
                ptype = self.eat('KEYWORD')
                if self.current() and self.current()[0] == 'IDENTIFIER':
                    pname = self.eat('IDENTIFIER')
                    if pname:
                        self.symbol_table.add(pname[1], ptype[1])
                if self.current() and self.current()[0] == 'COMMA':
                    self.pos += 1
            else:
                self.pos += 1

        self.expect('RPAREN', "Missing ')'")
        self.parse_block()

    def parse_function_def(self):
        self.eat('KEYWORD')       # return type
        self.eat('IDENTIFIER')    # function name
        self.eat('LPAREN')

        while self.current() and self.current()[0] != 'RPAREN':
            if self.is_type_keyword(self.current()):
                ptype = self.eat('KEYWORD')
                if self.current() and self.current()[0] == 'IDENTIFIER':
                    pname = self.eat('IDENTIFIER')
                    if pname:
                        self.symbol_table.add(pname[1], ptype[1])
                # optional comma
                if self.current() and self.current()[0] == 'COMMA':
                    self.pos += 1
            else:
                self.pos += 1

        self.expect('RPAREN', "Missing ')'")
        self.parse_block()

    # =========================================================
    # VARIABLE DECL
    # =========================================================

    def parse_var_declaration(self):
        t = self.eat('KEYWORD')
        dtype = t[1] if t else '?'

        if not self.current():
            return

        if self.current()[0] != 'IDENTIFIER':
            self.error("Expected variable name", self.current())
            self.skip_to('END')
            self.eat('END')
            return

        while True:
            name = self.eat('IDENTIFIER')
            if name:
                self.symbol_table.add(name[1], dtype)

            if self.current() and self.current()[0] == 'ASSIGN':
                self.pos += 1
                self.parse_expression()

            if self.current() and self.current()[0] == 'COMMA':
                self.pos += 1
                continue

            break

        self.expect('END', "Missing ';'")

    # =========================================================
    # ASSIGN
    # =========================================================

    def parse_assignment(self):
        self.eat('IDENTIFIER')
        self.eat('ASSIGN')
        self.parse_expression()
        self.expect('END', "Missing ';'")

    # =========================================================
    # IF / WHILE / FOR
    # =========================================================

    def parse_if(self):
        self.eat('KEYWORD')
        self.expect('LPAREN', "Missing '('")
        self.parse_expression()
        self.expect('RPAREN', "Missing ')'")
        self.parse_block_or_statement()

        while (self.current()
               and self.current()[0] == 'KEYWORD'
               and self.current()[1] == 'else'):
            self.pos += 1
            if self.current() and self.current()[1] == 'if':
                self.parse_if()
            else:
                self.parse_block_or_statement()

    def parse_while(self):
        self.eat('KEYWORD')
        self.expect('LPAREN', "Missing '('")
        self.parse_expression()
        self.expect('RPAREN', "Missing ')'")
        self.parse_block_or_statement()

    def parse_for(self):
        """
        for ( init ; condition ; update ) body

        init   : var-decl  OR  assignment  OR  empty
        condition : expression OR empty
        update : expression (including i++, i--, i=i+1)  OR  empty
        """
        self.eat('KEYWORD')   # 'for'
        self.expect('LPAREN', "Missing '('")

        # ---- init part ----
        if self.current() and self.current()[0] == 'END':
            # empty init
            self.pos += 1
        elif self.is_type_keyword(self.current()):
            # e.g.  int i = 0
            self.parse_for_var_decl()
        elif (self.current() and self.current()[0] == 'IDENTIFIER'
              and self.peek() and self.peek()[0] == 'ASSIGN'):
            # e.g.  i = 0
            self.eat('IDENTIFIER')
            self.eat('ASSIGN')
            self.parse_expression()
            self.expect('END', "Missing ';' in for-init")
        else:
            self.parse_expression()
            self.expect('END', "Missing ';' in for-init")

        # ---- condition part ----
        if self.current() and self.current()[0] == 'END':
            self.pos += 1   # empty condition
        else:
            self.parse_expression()
            self.expect('END', "Missing ';' in for-condition")

        # ---- update part ----
        if self.current() and self.current()[0] != 'RPAREN':
            if (self.current()[0] == 'IDENTIFIER'
                    and self.peek()
                    and self.peek()[0] in ('INCREMENT', 'DECREMENT')):
                self.pos += 2   # i++ / i--
            elif (self.current()[0] == 'IDENTIFIER'
                  and self.peek()
                  and self.peek()[0] == 'ASSIGN'):
                self.eat('IDENTIFIER')
                self.eat('ASSIGN')
                self.parse_expression()
            else:
                self.parse_expression()

        self.expect('RPAREN', "Missing ')'")
        self.parse_block_or_statement()

    def parse_for_var_decl(self):
        """
        Parse  type identifier = expr ;   inside for-init
        (no trailing ';' check — caller already did it)
        """
        t = self.eat('KEYWORD')
        dtype = t[1] if t else '?'

        if not self.current() or self.current()[0] != 'IDENTIFIER':
            self.error("Expected variable name in for-init", self.current())
            self.skip_to('END')
            self.eat('END')
            return

        name = self.eat('IDENTIFIER')
        if name:
            self.symbol_table.add(name[1], dtype)

        if self.current() and self.current()[0] == 'ASSIGN':
            self.pos += 1
            self.parse_expression()

        self.expect('END', "Missing ';' in for-init")

    # =========================================================
    # RETURN
    # =========================================================

    def parse_return(self):
        self.eat('KEYWORD')
        if self.current() and self.current()[0] != 'END':
            self.parse_expression()
        self.expect('END', "Missing ';'")

    # =========================================================
    # PRINT
    # =========================================================

    def parse_print(self):
        self.eat('KEYWORD')

        if self.current() and self.current()[0] == 'LPAREN':
            self.eat('LPAREN')
            while self.current() and self.current()[0] != 'RPAREN':
                self.parse_expression()
                if self.current() and self.current()[0] == 'COMMA':
                    self.pos += 1
            self.expect('RPAREN', "Missing ')'")
        else:
            self.parse_expression()

        self.expect('END', "Missing ';'")

    # =========================================================
    # BLOCKS
    # =========================================================

    def parse_block(self):
        self.expect('LBRACE', "Missing '{'")
        while self.current() and self.current()[0] != 'RBRACE':
            self.parse_statement()
        self.expect('RBRACE', "Missing '}'")

    def parse_block_or_statement(self):
        if self.current() and self.current()[0] == 'LBRACE':
            self.parse_block()
        else:
            self.parse_statement()

    # =========================================================
    # EXPRESSIONS
    # =========================================================

    def parse_expression(self):
        self.parse_unary()
        while self.current() and self.current()[0] in (
            'OP', 'REL_OP', 'LOGICAL_OP'
        ):
            self.pos += 1
            self.parse_unary()

    def parse_unary(self):
        tok = self.current()
        # unary minus / logical NOT
        if tok and tok[0] in ('OP', 'LOGICAL_OP') and tok[1] in ('-', '!'):
            self.pos += 1
        self.parse_primary()

    def parse_primary(self):
        tok = self.current()
        if not tok:
            return

        if tok[0] in ('NUMBER', 'STRING_LITERAL', 'CHAR_LITERAL'):
            self.pos += 1

        # *** FIX: true / false are KEYWORD tokens ***
        elif tok[0] == 'KEYWORD' and tok[1] in ('true', 'false'):
            self.pos += 1

        elif tok[0] == 'IDENTIFIER':
            self.pos += 1
            # function call:  foo(...)
            if self.current() and self.current()[0] == 'LPAREN':
                self.pos += 1
                while self.current() and self.current()[0] != 'RPAREN':
                    self.parse_expression()
                    if self.current() and self.current()[0] == 'COMMA':
                        self.pos += 1
                self.expect('RPAREN', "Missing ')' in function call")

        elif tok[0] == 'LPAREN':
            self.pos += 1
            self.parse_expression()
            self.expect('RPAREN', "Missing ')'")

        else:
            self.error(f"Unexpected token '{tok[1]}'", tok)
            self.pos += 1