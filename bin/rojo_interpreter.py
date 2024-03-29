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
    print("\033[1m\033[31mRojoInternals Error:\033[0m\n" + exctype.__name__ + ": " + str(value) + "\n" + traceback)

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
VARNAME_START = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz_$"
VARNAME_INTER = VARNAME_START + DIGITS

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

class NotDefinedError(RuntimeError):
    def __init__(self, pos_start, pos_end, context, details=''):
        super().__init__(pos_start, pos_end, context, "NotDefinedError", details)

class AlreadyDefinedError(RuntimeError):
    def __init__(self, pos_start, pos_end, context, details=''):
        super().__init__(pos_start, pos_end, context, "AlreadyDefinedError", details)

class TypeError_(RuntimeError):
    def __init__(self, pos_start, pos_end, context, details=''):
        super().__init__(pos_start, pos_end, context, "TypeError", details)

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

TT_INT         = "INT"
TT_FLOAT       = "FLOAT"
TT_IDENTIFIER  = "IDENTIFIER"
TT_KEYWORD     = "KEYWORD"
TT_PLUS        = "PLUS"
TT_MINUS       = "MINUS"
TT_MUL         = "MUL"
TT_DIV         = "DIV"
TT_MOD         = "MOD"
TT_POW         = "POW"
TT_EQ          = "EQ"
TT_LPAREN      = "LPAREN"
TT_RPAREN      = "RPAREN"
TT_EOF         = "EOF"

TT_ERROR       = "ERROR"

KEYWORDS = [
    "int",
    "float"
]

class Token:
    def __init__(self, type_, value=None, pos_start=None, pos_end=None):
        self.type = type_
        self.value = value

        if pos_start:
            self.pos_start = pos_start.copy()
            self.pos_end = pos_start.copy().advance()

        if pos_end:
            self.pos_end = pos_end.copy()

    def matches(self, type_, value):
        return type_ == self.type and value == self.value

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
            elif self.current_char in VARNAME_START:
                tokens.append(self.make_identifier())
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
            elif self.current_char == "=":
                tokens.append(Token(TT_EQ, pos_start=self.pos))
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

    def make_identifier(self):
        id_str = ''
        pos_start = self.pos.copy()

        while self.current_char != None and self.current_char in VARNAME_INTER:
            id_str += self.current_char
            self.advance()

        tok_type = TT_KEYWORD if id_str in KEYWORDS else TT_IDENTIFIER
        return Token(tok_type, id_str, pos_start, self.pos)

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

class VarAccessNode:
    def __init__(self, var_name_tok):
        self.var_name_tok = var_name_tok

        self.pos_start = self.var_name_tok.pos_start
        self.pos_end = self.var_name_tok.pos_end

    def __repr__(self):
        return str(self.var_name_tok)

class VarAssignNode:
    def __init__(self, type_, var_name_tok, value):
        self.type = type_
        self.var_name_tok = var_name_tok
        self.value = value
        self.used_type = self.type is not None

        if self.type:
            self.pos_start = self.type.pos_start
        else:
            self.pos_start = self.var_name_tok.pos_start

        self.pos_end = self.value.pos_end

    def __repr__(self):
        return f'VarAssignNode:({self.var_name_tok}, {self.value})'

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
        res = self.var_def()
        if not res.error and self.current_tok.type != TT_EOF:
            return res.failure(InvalidSyntaxError(
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

        elif tok.type == TT_IDENTIFIER:
            res.register(self.advance())
            return res.success(VarAccessNode(tok))

        elif tok.type == TT_LPAREN:
            res.register(self.advance())
            expr = res.register(self.var_def())
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

    def var_def(self):
        res = ParseResult()

        type_ = None
        var_name = None
        if self.current_tok.matches(TT_KEYWORD, "int"):
            type_ = self.current_tok
            res.register(self.advance())

            if self.current_tok.type != TT_IDENTIFIER:
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    "Expected identifier"
                ))

            var_name = self.current_tok
            res.register(self.advance())

            if self.current_tok.type != TT_EQ:
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    "Expected '='"
                ))

            res.register(self.advance())

        elif self.current_tok.matches(TT_KEYWORD, "float"):
            type_ = self.current_tok
            res.register(self.advance())

            if self.current_tok.type != TT_IDENTIFIER:
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    "Expected identifier"
                ))

            var_name = self.current_tok
            res.register(self.advance())

            if self.current_tok.type != TT_EQ:
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    "Expected '='"
                ))

            res.register(self.advance())
        elif self.current_tok.type == TT_IDENTIFIER:
            var_name = self.current_tok
            tmp = self.tok_idx
            res.register(self.advance())

            if self.current_tok.type == TT_EQ:
                res.register(self.advance())
            else:
                var_name = None
                self.tok_idx = tmp
                self.current_tok = self.tokens[tmp]

        expr = res.register(self.expr())
        if res.error:
            return res

        if var_name is None:
            return res.success(expr)
        else:
            return res.success(VarAssignNode(type_, var_name, expr))

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
        self.symbol_table = None

########################################
# SYMBOL TABLE
########################################

class SymbolTable:
    def __init__(self):
        self.symbols = {}
        self.types = {}
        self.parent = None

    def get(self, name):
        value = self.symbols.get(name, None)
        if value == None and self.parent:
            return self.parent.get(name)
        return value

    def set(self, type_, name, value):
        self.symbols[name] = value
        self.types[name] = type_

    def remove(self, name):
        del self.symbols[name]

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

    def visit_VarAccessNode(self, node, context):
        res = RuntimeResult()
        var_name = node.var_name_tok.value
        value = context.symbol_table.get(var_name)
        if value is None:
            return res.failure(NotDefinedError(
                node.pos_start, node.pos_end, context,
                "Variable `" + var_name + "` does not exist"
            ))

        if type(value).__name__ != "Number":
            return res.success(Number(value, type(value).__name__.upper()))
        return res.success(value)

    def visit_VarAssignNode(self, node, context):
        res = RuntimeResult()
        var_type = node.type
        var_name = node.var_name_tok.value
        value = res.register(self.visit(node.value, context))
        if res.error:
            return res

        if not var_type and context.symbol_table.get(var_name) is None:
            return res.failure(NotDefinedError(
                node.pos_start, node.pos_end, context,
                "Variable `" + var_name + "` does not exist"
            ))

        if context.symbol_table.get(var_name) is not None and var_type is not None:
            return res.failure(AlreadyDefinedError(
                node.pos_start, node.pos_end, context,
                "Cannot redefine variable `" + var_name + "`"
            ))

        if var_type and value.type.lower() != var_type.value:
            return res.failure(TypeError_(
                node.pos_start, node.pos_end, context,
                "Cannot place type `" + str(value.type).lower() + "` in `" + var_type.value + "`"
            ))

        if not var_type and value.type.lower() != context.symbol_table.types[var_name]:
            return res.failure(TypeError_(
                node.pos_start, node.pos_end, context,
                "Cannot place type `" + str(value.type).lower() + "` in `" + str(context.symbol_table.types[var_name]) + "`"
            ))

        if not var_type:
            context.symbol_table.set(context.symbol_table.types[var_name], var_name, value)
        else:
            context.symbol_table.set(var_type.value, var_name, value)

        if type(value).__name__ != "Number":
            return res.success(Number(value, type(value).__name__.upper()))
        return res.success(value)

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

global_symbol_table = SymbolTable()
global_symbol_table.set("int", "foo", 12)

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
    context.symbol_table = global_symbol_table
    result = interpreter.visit(ast, context)

    if result.error and settings["debug"]:
        print("\033[1m\033[31mInterpreter Error Encountered\033[0m")

    return result.value, result.error
