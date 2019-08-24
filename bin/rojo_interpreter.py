########################################
# CONSTANTS
########################################

DIGITS = '0123456789'

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

        return result

class IllegalCharacterError(Error):
    def __init__(self, pos_start, pos_end, details=''):
        super().__init__(pos_start, pos_end, 'IllegalCharacterError', details)

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

    def advance(self, current_char):
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

class Token:
    def __init__(self, type_, value=None):
        self.type = type_
        self.value = value

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
                tokens.append(Token(TT_PLUS))
                self.advance()
            elif self.current_char == "-":
                tokens.append(Token(TT_MINUS))
                self.advance()
            elif self.current_char == "*":
                tokens.append(Token(TT_MUL))
                self.advance()
            elif self.current_char == "/":
                tokens.append(Token(TT_DIV))
                self.advance()
            elif self.current_char == "(":
                tokens.append(Token(TT_LPAREN))
                self.advance()
            elif self.current_char == ")":
                tokens.append(Token(TT_RPAREN))
                self.advance()
            elif self.current_char == ".":
                tokens.append(self.make_number())
            else:
                pos_start = self.pos.copy()
                char = self.current_char
                self.advance()
                return [], IllegalCharacterError(pos_start, self.pos, "'" + char + "'")

        return tokens, None

    def make_number(self):
        num_str = ''
        dot = False

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
            return Token(TT_INT, int(num_str))
        return Token(TT_FLOAT, float(num_str))

########################################
# ENTRY (RUN)
########################################

def run(fname, code):
    lexer = Lexer(code, fname)
    tokens, error = lexer.lex()

    return tokens, error
