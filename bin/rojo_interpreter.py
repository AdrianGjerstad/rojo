########################################
# CONSTANTS
########################################

DIGITS = '0123456789'

########################################
# UTILITIES
########################################

# Code by CodePulse/David Callanan
# Modified for styling purposes
def arrow_string(text, pos_start, pos_end):
    result = ''

    # Calculate indices
    idx_start = max(text.rfind('\n', 0, pos_start.idx), 0)
    idx_end = text.find('\n', idx_start + 1)
    if idx_end < 0:
        idx_end = len(text)

    # Generate each line
    line_count = pos_end.ln - pos_start.ln + 1
    for i in range(line_count):
        # Calculate line columns
        line = text[idx_start:idx_end]
        col_start = pos_start.col if i == 0 else 0
        col_end = pos_end.col if i == line_count - 1 else len(line) - 1

        # Append to result
        result += line + '\n'
        result += ' ' * col_start + '^' * min(col_end - col_start, 1) + "~" * (col_end - col_start-1)

        # Re-calculate indices
        idx_start = idx_end
        idx_end = text.find('\n', idx_start + 1)
        if idx_end < 0:
            idx_end = len(text)

    return result.replace('\t', '')

########################################
# ERRORS
########################################

class Error:
    def __init__(self, pos_start, pos_end, error_name, details=''):
        self.pos_start = pos_start
        self.pos_end = pos_end
        self.error_name = error_name
        self.details = details

    def __repr__(self):
        result  = f'{self.error_name}{": " if self.details != "" else ""}{self.details}\n'
        result += f'File {self.pos_start.fname}, line {self.pos_start.ln + 1}'
        result += '\n\n' + arrow_string(self.pos_start.ftxt, self.pos_start, self.pos_end)

        return result

class IllegalCharacterError(Error):
    def __init__(self, pos_start, pos_end, details=''):
        super().__init__(pos_start, pos_end, 'IllegalCharacterError', details)

class InvalidSyntaxError(Error):
    def __init__(self, pos_start, pos_end, details=''):
        super().__init__(pos_start, pos_end, 'InvalidSyntaxError', details)

########################################
# POSITION
########################################

class Position:
    def __init__(self, idx, ln, col, fname, ftxt):
        self.idx = idx
        self.ln = ln
        self.col = col
        self.fname = fname
        self.ftxt = ftxt

    def advance(self, current_char=None):
        self.idx += 1
        self.col += 1

        if current_char == "\n":
            self.ln += 1
            self.col = 0

        return self

    def copy(self):
        return Position(self.idx, self.ln, self.col, self.fname, self.ftxt)

########################################
# TOKENS
########################################

TT_INT     = "INT"
TT_FLOAT   = "FLOAT"
TT_PLUS    = "PLUS"
TT_MINUS   = "MINUS"
TT_MUL     = "MUL"
TT_DIV     = "DIV"
TT_LPAREN  = "LPAREN"
TT_RPAREN  = "RPAREN"
TT_EOF     = "EOF"

class Token:
    def __init__(self, type_, value=None, pos_start=None, pos_end=None):
        self.type = type_
        self.value = value

        if pos_start:
            self.pos_start = pos_start.copy()
            self.pos_end = pos_start.copy().advance()

        if pos_end:
            self.pos_end = pos_end.copy()

    def __repr__(self):
        if self.value is not None:
            return f'{self.type}:{self.value}'
        return f'{self.type}'

########################################
# LEXER
########################################

class Lexer:
    def __init__(self, code, fname):
        self.code = code
        self.pos = Position(-1, 0, -1, fname, code)
        self.current_char = None
        self.advance()

    def advance(self):
        self.pos.advance(self.current_char)
        self.current_char = self.code[self.pos.idx] if self.pos.idx < len(self.code) else None

    def lex(self):
        tokens = []

        while self.current_char is not None:
            if self.current_char in ' \t':
                # Skip whitespace
                self.advance()
            elif self.current_char in DIGITS:
                tokens.append(self.make_number())
            elif self.current_char == "+":
                tokens.append(Token(TT_PLUS, pos_start=self.pos))
                self.advance()
            elif self.current_char == "-":
                tokens.append(Token(TT_MINUS, pos_start=self.pos))
                self.advance()
            elif self.current_char == "*":
                tokens.append(Token(TT_MUL, pos_start=self.pos))
                self.advance()
            elif self.current_char == "/":
                tokens.append(Token(TT_DIV, pos_start=self.pos))
                self.advance()
            elif self.current_char == "(":
                tokens.append(Token(TT_LPAREN, pos_start=self.pos))
                self.advance()
            elif self.current_char == ")":
                tokens.append(Token(TT_RPAREN, pos_start=self.pos))
                self.advance()
            elif self.current_char == ".":
                tokens.append(self.make_number())
            else:
                pos_start = self.pos.copy()
                char = self.current_char
                self.advance()
                return [], IllegalCharacterError(pos_start, self.pos, "'" + char + "'")

        tokens.append(Token(TT_EOF, pos_start=self.pos))
        return tokens, None

    def make_number(self):
        num_str = ''
        dot = False
        pos_start = self.pos.copy()

        while self.current_char is not None and self.current_char in DIGITS + '.':
            if self.current_char == ".":
                if dot:
                    break
                dot = True
                num_str += "."
            else:
                num_str += self.current_char

            self.advance()

        if not dot:
            return Token(TT_INT, int(num_str), pos_start, self.pos)
        return Token(TT_FLOAT, float(num_str), pos_start, self.pos)

########################################
# NODES
########################################

class NumberNode:
    def __init__(self, tok):
        self.tok = tok

    def __repr__(self):
        return f'{self.tok}'

class BinOpNode:
    def __init__(self, left_node, op_tok, right_node):
        self.left_node = left_node
        self.op_tok = op_tok
        self.right_node = right_node

    def __repr__(self):
        return f'({self.left_node}, {str(self.op_tok)}, {self.right_node})'

class UnaryOpNode:
    def __init__(self, op_tok, node):
        self.op_tok = op_tok
        self.node = node

    def __repr__(self):
        return f'({self.op_tok}, {self.node})'

########################################
# PARSE RESULT
########################################

class ParseResult:
    def __init__(self):
        self.error = None
        self.node = None

    def register(self, res):
        if isinstance(res, ParseResult):
            if res.error:
                self.error = res.error
            return res.node

        return res

    def success(self, node):
        self.node = node
        return self

    def failure(self, error):
        self.error = error
        return self

########################################
# PARSER
########################################

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.tok_idx = -1
        self.current_tok = None
        self.advance()

    def advance(self):
        self.tok_idx += 1
        if self.tok_idx < len(self.tokens):
            self.current_tok = self.tokens[self.tok_idx]

    ########################################

    def parse(self):
        res = self.expr()
        if not res.error and self.current_tok.type != TT_EOF:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected '+', '-', '*', or '/'"
            ))
        return res

    ########################################

    def factor(self):
        res = ParseResult()

        tok = self.current_tok

        if tok.type in (TT_PLUS, TT_MINUS):
            res.register(self.advance())
            factor = res.register(self.factor())
            if res.error:
                return res
            return res.success(UnaryOpNode(tok, factor))

        elif tok.type in (TT_INT, TT_FLOAT):
            res.register(self.advance())
            return res.success(NumberNode(tok))

        elif tok.type == TT_LPAREN:
            res.register(self.advance())
            expr = res.register(self.expr())
            if res.error:
                return res
            if self.current_tok.type == TT_RPAREN:
                res.register(self.advance())
                return res.success(expr)
            else:
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    "Expected ')'"
                ))

        return res.failure(InvalidSyntaxError(
            tok.pos_start, tok.pos_end,
            "Expected int or float"
        ))

    def term(self):
        return self.bin_op(self.factor, (TT_MUL, TT_DIV))

    def expr(self):
        return self.bin_op(self.term, (TT_PLUS, TT_MINUS))

    ########################################

    def bin_op(self, func, ops):
        res = ParseResult()

        left = res.register(func())
        if res.error:
            return res

        while self.current_tok.type in ops:
            op_tok = self.current_tok
            res.register(self.advance())
            right = res.register(func())
            if res.error:
                return res
            left = BinOpNode(left, op_tok, right)

        return res.success(left)

########################################
# ENTRY (RUN)
########################################

def run(fname, code):
    # Lex the code given to us by ROSH or the command line
    lexer = Lexer(code, fname)
    tokens, error = lexer.lex()

    if error:
        return None, error

    # Generate AbstractSyntaxTree with the tokens from the lexer
    parser = Parser(tokens)
    ast = parser.parse()

    return ast.node, ast.error
