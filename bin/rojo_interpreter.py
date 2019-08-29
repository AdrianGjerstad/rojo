#!/usr/bin/env python3

# The shebang line above is not neccessary, but for a complete look, it should
# exist.

########################################
# IMPORTS
########################################

import sys
import os

########################################
# GLOBAL EXCEPTION HANDLER
########################################

def my_except_hook(exctype, value, traceback):
    print("\033[1m\033[31mRojoInternals Error:\033[0m\n" + exctype.__name__ + ": " + str(value))

    args = []

    for i in range(len(sys.argv)-1):
        args.append(sys.argv[i+1])
    if len(args) != 0:
        approved = args.copy()
        for i in range(len(approved)):
            if approved[i].startswith("--private_"):
                approved.pop(i)
                i -= 1

    args.insert(0, "--private_revived")
    args.insert(0, "arg_placeholder")
    print("\033[1m\033[35mReviving...\033[0m")
    os.execvp(sys.argv[0], args)

sys.excepthook = my_except_hook

########################################
# EXTERNALS
########################################

version = "1.0.0"

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

class RuntimeError(Error):
    def __init__(self, pos_start, pos_end, context, name='RuntimeError', details=''):
        super().__init__(pos_start, pos_end, name, details)
        self.context = context

    def __repr__(self):
        result  = self.generate_traceback()
        result += f'{self.error_name}{": " if self.details != "" else ""}{self.details}'
        result += '\n\n' + arrow_string(self.pos_start.ftxt, self.pos_start, self.pos_end)

        return result

    def generate_traceback(self):
        result = ''
        pos = self.pos_start
        ctx = self.context

        while ctx:
            result = f'  File {pos.fname}, line {str(pos.ln + 1)}, in {ctx.display_name}\n' + result
            pos = ctx.parent_entry_pos
            ctx = ctx.parent

        return "Stack trace (Most recent last):\n" + result

class DivisionByZeroError(RuntimeError):
    def __init__(self, pos_start, pos_end, context, details=''):
        super().__init__(pos_start, pos_end, context, "DivisionByZeroError", details)

class RangeError(RuntimeError):
    def __init__(self, pos_start, pos_end, context, details=''):
        super().__init__(pos_start, pos_end, context, "RangeError", details)

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
TT_MOD     = "MOD"
TT_POW     = "POW"
TT_LPAREN  = "LPAREN"
TT_RPAREN  = "RPAREN"
TT_EOF     = "EOF"

TT_ERROR   = "ERROR"

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
                token, error = self.make_number()

                if error:
                    tokens.append(Token(TT_ERROR, self.current_char))
                    return tokens, error

                tokens.append(token)
            elif self.current_char == "+":
                tokens.append(Token(TT_PLUS, pos_start=self.pos))
                self.advance()
            elif self.current_char == "-":
                tokens.append(Token(TT_MINUS, pos_start=self.pos))
                self.advance()
            elif self.current_char == "*":
                tokens.append(self.make_pow_or_mul())
            elif self.current_char == "/":
                tokens.append(Token(TT_DIV, pos_start=self.pos))
                self.advance()
            elif self.current_char == "%":
                tokens.append(Token(TT_MOD, pos_start=self.pos))
                self.advance()
            elif self.current_char == "(":
                tokens.append(Token(TT_LPAREN, pos_start=self.pos))
                self.advance()
            elif self.current_char == ")":
                tokens.append(Token(TT_RPAREN, pos_start=self.pos))
                self.advance()
            elif self.current_char == ".":
                token, error = self.make_number()

                if error:
                    tokens.append(Token(TT_ERROR, self.current_char))
                    return tokens, error

                tokens.append(token)
            else:
                pos_start = self.pos.copy()
                char = self.current_char
                self.advance()

                tokens.append(Token(TT_ERROR, char))
                return tokens, IllegalCharacterError(pos_start, self.pos, "'" + char + "'")

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

        if num_str == '.':
            return None, IllegalCharacterError(
                pos_start.advance(), self.pos.copy().advance(),
                "'" + self.current_char + "'"
            )

        if not dot:
            return Token(TT_INT, int(num_str), pos_start, self.pos), None
        return Token(TT_FLOAT, float(num_str), pos_start, self.pos), None

    def make_pow_or_mul(self):
        pos_start = self.pos.copy()

        self.advance()
        if self.current_char == "*":
            self.advance()
            return Token(TT_POW, pos_start=pos_start, pos_end=self.pos)

        return Token(TT_MUL, pos_start=pos_start, pos_end=self.pos)

########################################
# NODES
########################################

class AbstractSyntaxTree:
    def __init__(self, node=None):
        self.node = node

    def __repr__(self):
        return str(self.node)

class ValueNode:
    pass

class IntegerNode(ValueNode):
    def __init__(self, tok):
        self.tok = tok

        self.pos_start = self.tok.pos_start
        self.pos_end = self.tok.pos_end

    def __repr__(self):
        return f'{self.tok}'

class FloatNode(ValueNode):
    def __init__(self, tok):
        self.tok = tok

        self.pos_start = self.tok.pos_start
        self.pos_end = self.tok.pos_end

    def __repr__(self):
        return f'{self.tok}'

class BinOpNode:
    def __init__(self, left_node, op_tok, right_node):
        self.left_node = left_node
        self.op_tok = op_tok
        self.right_node = right_node

        self.pos_start = self.left_node.pos_start
        self.pos_end = self.right_node.pos_end

    def __repr__(self):
        return f'BinOpNode:({self.left_node}, {str(self.op_tok)}, {self.right_node})'

class UnaryOpNode:
    def __init__(self, op_tok, node):
        self.op_tok = op_tok
        self.node = node

        self.pos_start = self.op_tok.pos_start
        self.pos_end = self.node.pos_end

    def __repr__(self):
        return f'UnaryOpNode:({self.op_tok}, {self.node})'

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

    def failure(self, node, error):
        self.node = node
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
            return res.failure(res.node, InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected '+', '-', '*', '/',  '**'"
            )).node, res.error
        if res.error:
            return AbstractSyntaxTree(res.node), res.error
        return AbstractSyntaxTree(res.node), res.error

    ########################################

    def unit(self):
        res = ParseResult()

        tok = self.current_tok

        if tok.type in (TT_INT):
            res.register(self.advance())
            return res.success(IntegerNode(tok))

        elif tok.type in (TT_FLOAT):
            res.register(self.advance())
            return res.success(FloatNode(tok))

        elif tok.type == TT_LPAREN:
            res.register(self.advance())
            expr = res.register(self.expr())
            if res.error:
                return res
            if self.current_tok.type == TT_RPAREN:
                res.register(self.advance())
                return res.success(expr)
            else:
                return res.failure(expr, InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    "Expected ')'"
                ))

        return res.failure(res.node, InvalidSyntaxError(
            tok.pos_start, tok.pos_end,
            "Expected int, float, or '('"
        ))

    def power(self):
        return self.bin_op(self.unit, (TT_POW,), self.factor)

    def factor(self):
        res = ParseResult()

        tok = self.current_tok

        if tok.type in (TT_PLUS, TT_MINUS):
            res.register(self.advance())
            factor = res.register(self.factor())
            if res.error:
                return res
            return res.success(UnaryOpNode(tok, factor))

        return self.power()

    def term(self):
        return self.bin_op(self.factor, (TT_MUL, TT_DIV, TT_MOD))

    def expr(self):
        return self.bin_op(self.term, (TT_PLUS, TT_MINUS))

    ########################################

    def bin_op(self, func_a, ops, func_b=None):
        if func_b is None:
            func_b = func_a

        res = ParseResult()

        left = res.register(func_a())
        if res.error:
            return res

        while self.current_tok.type in ops:
            op_tok = self.current_tok
            res.register(self.advance())
            right = res.register(func_b())
            if res.error:
                return res
            left = BinOpNode(left, op_tok, right)

        return res.success(left)

########################################
# RUNTIME RESULT
########################################

class RuntimeResult:
    def __init__(self):
        self.error = None
        self.value = None

    def register(self, res):
        if res.error:
            self.error = res.error
        return res.value

    def success(self, value):
        self.value = value
        return self

    def failure(self, error):
        self.error = error
        return self

########################################
# VALUES
########################################

class Number:
    def __init__(self, value, type_):
        self.value = value
        self.type = type_
        self.set_pos()
        self.set_context()

    def set_pos(self, pos_start=None, pos_end=None):
        self.pos_start = pos_start
        self.pos_end = pos_end
        return self

    def set_context(self, context=None):
        self.context = context
        return self

    def added_to(self, other):
        if isinstance(other, Number):
            type_ = TT_FLOAT if self.type == TT_FLOAT or other.type == TT_FLOAT else TT_INT
            return Number(self.value + other.value, type_).set_context(self.context), None

    def subbed_by(self, other):
        if isinstance(other, Number):
            type_ = TT_FLOAT if self.type == TT_FLOAT or other.type == TT_FLOAT else TT_INT
            return Number(self.value - other.value, type_).set_context(self.context), None

    def multed_by(self, other):
        if isinstance(other, Number):
            type_ = TT_FLOAT if self.type == TT_FLOAT or other.type == TT_FLOAT else TT_INT
            val = Number(self.value * other.value, type_).set_context(self.context)

            return val, None

    def dived_by(self, other):
        if isinstance(other, Number):
            if other.value == 0:
                return None, DivisionByZeroError(
                    other.pos_start, other.pos_end, self.context,
                    "Division by zero"
                )

            type_ = TT_FLOAT if self.type == TT_FLOAT or other.type == TT_FLOAT else "unk"
            val =  Number(self.value / other.value, type_).set_context(self.context)
            if val.type == "unk" and val.value == int(val.value):
                val.type = TT_INT
            else:
                val.type = TT_FLOAT

            return val, None

    def modded_by(self, other):
        if isinstance(other, Number):
            if other.value == 0:
                return None, DivisionByZeroError(
                    other.pos_start, other.pos_end, self.context,
                    "Division by zero"
                )

            type_ = TT_FLOAT if self.type == TT_FLOAT or other.type == TT_FLOAT else "unk"
            val =  Number(self.value % other.value, type_).set_context(self.context)
            if val.type == "unk" and val.value == int(val.value):
                val.type = TT_INT
            else:
                val.type = TT_FLOAT

            return val, None

    def powed_by(self, other):
        if isinstance(other, Number):
            type_ = TT_FLOAT if self.type == TT_FLOAT or other.type == TT_FLOAT else TT_INT
            val = Number(self.value ** other.value, type_).set_context(self.context)
            if type(val.value).__name__ == "complex":
                sign = "+" if val.value.imag >= 0 else "-"
                return None, RangeError(
                    self.pos_start, other.pos_end, self.context,
                    "pow(x, y) where x < 0 and y is not whole has undefined behavior.\n(Complex number created: " +
                    str(val.value.real) + sign + str(abs(val.value.imag)) + "i)"
                )

            if val.value == int(val.value):
                val.type = TT_INT

            return val, None

    def __repr__(self):
        if self.type == TT_INT:
            return str(int(self.value))

        return str(float(self.value))

########################################
# CONTEXT
########################################

class Context:
    def __init__(self, display_name, parent=None, parent_entry_pos=None):
        self.display_name = display_name
        self.parent = parent
        self.parent_entry_pos = parent_entry_pos

########################################
# INTERPRETER
########################################

class Interpreter:
    def __init__(self):
        pass

    def visit(self, node, context):
        method_name = f'visit_{type(node).__name__}'
        method = getattr(self, method_name, self.no_visit)
        return method(node, context)

    ########################################

    def no_visit(self, node, context):
        raise Exception("No visit method for " + type(node).__name__ + " class.")

    ########################################

    def visit_AbstractSyntaxTree(self, node, context):
        res = RuntimeResult()

        node_ = res.register(self.visit(node.node, context))

        if res.error:
            return res

        return res.success(node_)

    def visit_IntegerNode(self, node, context):
        return RuntimeResult().success(
            Number(node.tok.value, TT_INT).set_pos(node.pos_start, node.pos_end).set_context(context))

    def visit_FloatNode(self, node, context):
        return RuntimeResult().success(
            Number(node.tok.value, TT_FLOAT).set_pos(node.pos_start, node.pos_end).set_context(context))

    def visit_BinOpNode(self, node, context):
        res = RuntimeResult()

        left = res.register(self.visit(node.left_node, context))
        if res.error:
            return res
        right = res.register(self.visit(node.right_node, context))
        if res.error:
            return res

        if node.op_tok.type == TT_PLUS:
            result, error = left.added_to(right)
        elif node.op_tok.type == TT_MINUS:
            result, error = left.subbed_by(right)
        elif node.op_tok.type == TT_MUL:
            result, error = left.multed_by(right)
        elif node.op_tok.type == TT_DIV:
            result, error = left.dived_by(right)
        elif node.op_tok.type == TT_MOD:
            result, error = left.modded_by(right)
        elif node.op_tok.type == TT_POW:
            result, error = left.powed_by(right)

        if error:
            return res.failure(error)

        return res.success(result.set_pos(node.pos_start, node.pos_end))

    def visit_UnaryOpNode(self, node, context):
        res = RuntimeResult()

        number = res.register(self.visit(node.node, context))
        if res.error:
            return res

        error = None

        if node.op_tok.type == TT_MINUS:
            number, error = number.multed_by(Number(-1, TT_INT))

        if error:
            return res.failure(error)

        return res.success(number.set_pos(node.pos_start, node.pos_end))

########################################
# ENTRY (RUN)
########################################

def run(fname, code, settings):
    # Lex the code given to us by ROSH or the command line
    lexer = Lexer(code, fname)
    tokens, error = lexer.lex()

    if settings["debug"]:
        print("\033[1m\033[33mtok\033[0m   \033[1m\033[34m>\033[0m " + str(tokens))

    if error:
        if settings["debug"]:
            print("\033[1m\033[33mast\033[0m   \033[1m\033[34m>\033[0m Unavailable (Parser Not Reached)")
            print("\033[1m\033[31mLexing Error Encountered\033[0m")
        return None, error

    # Generate AbstractSyntaxTree with the tokens from the lexer
    parser = Parser(tokens)
    ast, error = parser.parse()
    if settings["debug"] and not error:
        print("\033[1m\033[33mast\033[0m   \033[1m\033[34m>\033[0m " + str(ast))

    if error:
        if settings["debug"]:
            print("\033[1m\033[33mast\033[0m   \033[1m\033[34m>\033[0m Unavailable (Parser Error)")
            print("\033[1m\033[31mParsing Error Encountered\033[0m")
        return ast, error

    # Execute code according to the AST from the parser
    interpreter = Interpreter()
    context = Context('<global>')
    result = interpreter.visit(ast, context)

    if result.error and settings["debug"]:
        print("\033[1m\033[31mInterpreter Error Encountered\033[0m")

    return result.value, result.error
