import re


class Lexer:

    def __init__(self, code):
        self.code = code

    # =====================================================
    # TOKEN SPECIFICATION
    # =====================================================

    token_specification = [

        # COMMENTS
        ('COMMENT_SINGLE', r'//.*'),
        ('COMMENT_MULTI', r'/\*[\s\S]*?\*/'),

        # STRINGS & CHARS
        ('STRING_LITERAL', r'"([^"\\]|\\.)*"'),
        ('CHAR_LITERAL', r"'([^'\\]|\\.)'"),

        # KEYWORDS
        ('KEYWORD',
         r'\b(int|float|double|char|void|string|bool|if|else|for|while|return|print|true|false)\b'),

        # OPERATORS
        ('INCREMENT', r'\+\+'),
        ('DECREMENT', r'--'),

        ('LOGICAL_OP', r'&&|\|\||!'),

        ('REL_OP', r'==|!=|<=|>=|<|>'),

        ('ASSIGN', r'='),

        ('OP', r'[\+\-\*/%]'),

        # SYMBOLS
        ('LPAREN', r'\('),
        ('RPAREN', r'\)'),

        ('LBRACE', r'\{'),
        ('RBRACE', r'\}'),

        ('LBRACKET', r'\['),
        ('RBRACKET', r'\]'),

        ('COMMA', r','),

        ('END', r';'),

        # NUMBERS
        ('NUMBER', r'\d+(\.\d+)?'),

        # IDENTIFIERS
        ('IDENTIFIER', r'[A-Za-z_][A-Za-z0-9_]*'),

        # WHITESPACE
        ('NEWLINE', r'\r?\n'),
        ('SKIP', r'[ \t\r]+'),

        # INVALID
        ('MISMATCH', r'.'),
    ]

    # =====================================================
    # TOKENIZER
    # =====================================================

    def tokenize(self):

        tok_regex = '|'.join(
            '(?P<%s>%s)' % pair
            for pair in self.token_specification
        )

        tokens = []

        line_num = 1
        line_start = 0

        for mo in re.finditer(tok_regex, self.code):

            kind = mo.lastgroup
            value = mo.group()

            column = mo.start() - line_start

            # =============================================
            # NEWLINE
            # =============================================

            if kind == 'NEWLINE':

                line_num += 1
                line_start = mo.end()

                continue

            # =============================================
            # SKIP WHITESPACE
            # =============================================

            if kind == 'SKIP':
                continue

            # =============================================
            # SKIP COMMENTS
            # =============================================

            if kind in [
                'COMMENT_SINGLE',
                'COMMENT_MULTI'
            ]:
                continue

            # =============================================
            # INVALID CHARACTER
            # =============================================

            if kind == 'MISMATCH':

                tokens.append((
                    'ERROR',
                    f'Unexpected character: {value}',
                    line_num,
                    column
                ))

                continue

            # =============================================
            # NORMAL TOKENS
            # =============================================

            tokens.append((
                kind,
                value,
                line_num,
                column
            ))

        return tokens