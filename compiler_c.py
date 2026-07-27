# -*- coding: utf-8 -*-
import re

TOKEN_SPEC = [
     #Multi_Line_Comment
    ("ML_COMMENT", r"/\*[\s\S]*?\*/"),
    
    #  Keywords
    ("MAIN", r"رئيسي"),
    ("PRINT", r"اطبع"),
    ("INPUT", r"ادخل"),
    ("IF", r"اذا"),
    ("ELSE_IF", r"او اذا"),
    ("ELSE", r"اذا لم"),
    ("WHILE", r"بينما"),
    ("REPEAT", r"تكرار"),
    ("RETURN", r"ارجع"),
    ("IMPORT", r"استيراد"),
    ("BREAK", r"قف"),

    # Data types
    ("INT_TYPE", r"رقم"),
    ("FLOAT_TYPE", r"عشري"),
    ("STRING_TYPE", r"نص"),
    ("BOOL_TYPE", r"منطقي"),

    # Literals
    ("FLOAT", r"\d+\.\d+"),
    ("BOOL", r"\b(0|1)\b"),
    ("INT", r"\d+"),
    ("STRING", r'"([^"\\]|\\.)*"'),


    # Operators
    ("EQ", r"=="),
    ("NE", r"!="),
    ("LE", r"<="),
    ("GE", r">="),
    ("LT", r"<"),
    ("GT", r">"),
    ("ASSIGN", r"="),
    ("PLUS", r"\+"),
    ("MINUS", r"-"),
    ("MUL", r"\*"),
    ("DIV", r"/"),

    # Punctuation
    ("LPAREN", r"\("),
    ("RPAREN", r"\)"),
    ("LBRACE", r"\{"),
    ("RBRACE", r"\}"),
    ("SEMI", r"[;.]"),
    ("COMMA", r","),

    # Identifier
    ("ID", r"[ء-يA-Za-z_][ء-يA-Za-z0-9_]*"),

    # Comments
    ("COMMENT", r"#.*"),

    # Whitespace
    ("NEWLINE", r"\n"),
    ("SKIP", r"[ \t]+"),

    # Error
    ("MISMATCH", r"."),
]

master_pattern = re.compile(
    "|".join(f"(?P<{name}>{pattern})" for name, pattern in TOKEN_SPEC)
)


# Scanner Function.............................................................................................................................

def scan(code):
    tokens = []
    line = 1

    for match in re.finditer(master_pattern, code):
        kind = match.lastgroup
        value = match.group()
        start = match.start()

        if kind == "NEWLINE":
            line += 1
            continue
        elif kind == "SKIP" or kind == "COMMENT" or kind == "ML_COMMENT":
            continue
        elif kind == "MISMATCH":
            raise RuntimeError(f"Unexpected character {value} at line {line}")
        else:
            tokens.append({
                "type": kind,
                "value": value,
                "pos": start,
                "line": line
            })

    return tokens



# Test
# with open("/content/test.txt", "r", encoding="utf-8") as f:
#     code = f.read()

#     tokens = scan(code)
#     for t in tokens:
#         print(t)

from dataclasses import dataclass, field

# AST Node..................................................................
@dataclass
class STNode:
    type: str
    value: str = ""
    dtype: str = ""
    children: list = field(default_factory=list)

# Parser.....................................................................
class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def current(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def match(self, token_type):
        token = self.current()
        if token and token["type"] == token_type:
            self.pos += 1
            return token
        raise Exception(f"[Parser Error] Expected {token_type}, got {token} at pos {self.pos}")

    def parse(self):
        node = self.program()
        if self.current() is not None:
            raise Exception("Unexpected tokens after program end")
        return node

    def program(self):
        node = STNode("PROGRAM")
        node.children.append(self.main_function())
        return node

    def main_function(self):
        self.match("INT_TYPE")
        self.match("MAIN")
        self.match("LPAREN")
        self.match("RPAREN")
        body = self.block()
        return STNode("MAIN_FUNC", children=[body])

    def block(self):
        self.match("LBRACE")

        stmts = []
        while self.current() and self.current()["type"] != "RBRACE":
            stmts.append(self.statement())

        if not self.current():
            raise Exception("Missing closing '}'")

        self.match("RBRACE")
        return STNode("BLOCK", children=stmts)

    def statement(self):
        token = self.current()

        if token["type"] in ("INT_TYPE", "FLOAT_TYPE", "STRING_TYPE", "BOOL_TYPE"):
            return self.declaration()
        elif token["type"] == "PRINT":
            return self.print_stmt()
        elif token["type"] == "INPUT":
            return self.input_stmt()
        elif token["type"] == "IF":
            return self.if_stmt()
        elif token["type"] == "WHILE":
            return self.while_stmt()
        elif token["type"] == "REPEAT":
            return self.for_stmt()
        else:
            return self.assignment()

    def declaration(self, expect_semi=True):
        dtype = self.match(self.current()["type"])["value"]
        name = self.match("ID")["value"]
        self.match("ASSIGN")
        expr = self.expr()

        if expect_semi:
            self.match("SEMI")

        return STNode("DECL", value=name, dtype=dtype, children=[expr])
    

    def assignment(self, expect_semi=True):
        name = self.match("ID")["value"]
        self.match("ASSIGN")
        expr = self.expr()

        if expect_semi:
            self.match("SEMI")

        return STNode("ASSIGN", value=name, children=[expr])

    def input_stmt(self):
        self.match("INPUT")
        self.match("LPAREN")
        var_name = self.match("ID")["value"]
        self.match("RPAREN")
        self.match("SEMI")
        return STNode("INPUT", value=var_name)

    def print_stmt(self):
        self.match("PRINT")
        self.match("LPAREN")
        expr = self.expr()
        self.match("RPAREN")
        self.match("SEMI")
        return STNode("PRINT", children=[expr])

    def if_stmt(self):
        self.match("IF")
        self.match("LPAREN")
        cond = self.expr()
        self.match("RPAREN")

        then_block = self.block()

        else_block = None
        if self.current() and self.current()["type"] == "ELSE":
            self.match("ELSE")
            else_block = self.block()

        children = [cond, then_block]
        if else_block:
            children.append(else_block)

        return STNode("IF", children=children)

    def while_stmt(self):
        self.match("WHILE")
        self.match("LPAREN")
        condition = self.expr()
        self.match("RPAREN")
        body = self.block()
        return STNode("WHILE", children=[condition, body])

    def for_stmt(self):
        self.match("REPEAT")
        self.match("LPAREN")

        if self.current()["type"] in ("INT_TYPE", "FLOAT_TYPE"):
            init = self.declaration(expect_semi=False)
        else:
            init = self.assignment(expect_semi=False)

        self.match("SEMI")

        condition = self.expr()
        self.match("SEMI")

        update = self.assignment(expect_semi=False)

        self.match("RPAREN")
        body = self.block()

        return STNode("FOR", children=[init, condition, update, body])

    # EXPRESSIONS (precedence)
    def expr(self):
        return self.rel_expr()

    def rel_expr(self):
        left = self.add_expr()
        while self.current() and self.current()["type"] in ("LT","GT","LE","GE","EQ","NE"):
            op = self.match(self.current()["type"])["value"]
            right = self.add_expr()
            left = STNode("BINOP", value=op, children=[left, right])
        return left

    def add_expr(self):
        left = self.term()
        while self.current() and self.current()["type"] in ("PLUS","MINUS"):
            op = self.match(self.current()["type"])["value"]
            right = self.term()
            left = STNode("BINOP", value=op, children=[left, right])
        return left

    def term(self):
        left = self.factor()
        while self.current() and self.current()["type"] in ("MUL","DIV"):
            op = self.match(self.current()["type"])["value"]
            right = self.factor()
            left = STNode("BINOP", value=op, children=[left, right])
        return left

    def factor(self):
        token = self.current()

        if token["type"] == "INT":
            return STNode("INT", value=self.match("INT")["value"])

        elif token["type"] == "FLOAT":
            return STNode("FLOAT", value=self.match("FLOAT")["value"])

        elif token["type"] == "BOOL":
            return STNode("BOOL", value=self.match("BOOL")["value"])  

        elif token["type"] == "STRING":
            return STNode("STRING", value=self.match("STRING")["value"])

        elif token["type"] == "ID":
            return STNode("ID", value=self.match("ID")["value"])

        elif token["type"] == "MINUS":
            self.match("MINUS")
            node = self.factor()
            return STNode("UNARY", value="-", children=[node])

        elif token["type"] == "LPAREN":
            self.match("LPAREN")
            node = self.expr()
            self.match("RPAREN")
            return node

        raise Exception(f"Invalid expression at pos {self.pos}")

def print_tree(node, level=0):
    print("  " * level + f"{node.type} ({node.value})")
    for child in node.children:
        if child:
            print_tree(child, level + 1)

# -----------------------------
# tokens = scan(code)
# parser = Parser(tokens)
# tree = parser.parse()
# print_tree(tree)

# SYMBOL TABLE............................................................

class SymbolTable:
    def __init__(self):
        self.scopes = [{}]

    def push(self):
        self.scopes.append({})

    def pop(self):
        self.scopes.pop()

    def declare(self, name, dtype):
        if name in self.scopes[-1]:
            raise Exception(f"Variable '{name}' already declared")

        self.scopes[-1][name] = dtype

    def lookup(self, name):
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]

        raise Exception(f"Undeclared variable '{name}'")


# SEMANTIC ANALYZER + CODE GENERATOR..........................................

class SemanticAnalyzer:

    def __init__(self):

        self.symbols = SymbolTable()

        # generated cpp lines
        self.cpp_code = []

        # indentation
        self.indent = 1

    # HELPERS....................

    def emit(self, line):
        self.cpp_code.append("    " * self.indent + line)

    def enter_scope(self):
        self.emit("{")
        self.indent += 1

    def exit_scope(self):
        self.indent -= 1
        self.emit("}")

    def get_code(self):
        return "\n".join(self.cpp_code)

    # MAIN ANALYZE......................

    def analyze(self, node):

        if node is None:
            return None

        method = getattr(
            self,
            f"visit_{node.type}",
            self.generic
        )

        return method(node)

    def generic(self, node):

        for child in node.children:
            if child is not None:
                self.analyze(child)

    # TYPE MAPPING.......................................................

    def map_type(self, dtype):

        mapping = {
            "رقم": "INT",
            "عشري": "FLOAT",
            "نص": "STRING",
            "منطقي": "BOOL"
        }

        return mapping.get(dtype, dtype)

    def to_cpp_type(self, dtype):

        mapping = {
            "INT": "int",
            "FLOAT": "float",
            "STRING": "string",
            "BOOL": "bool"
        }

        return mapping[dtype]

    # DECLARATION................................................

    def visit_DECL(self, node):

        expr_type = self.analyze(node.children[0])

        var_type = self.map_type(node.dtype)

        # السماح بـ BOOL -> INT
        if var_type == "INT" and expr_type == "BOOL":
            expr_type = "INT"

        if expr_type != var_type:
            raise Exception(
                f"Cannot assign {expr_type} to {var_type}"
            )

        self.symbols.declare(node.value, var_type)

        cpp_type = self.to_cpp_type(var_type)

        expr_code = self.expr_to_cpp(node.children[0])

        self.emit(
            f"{cpp_type} {node.value} = {expr_code};"
        )

    # ASSIGNMENT.......................................................

    def visit_ASSIGN(self, node):

        var_type = self.symbols.lookup(node.value)

        expr_type = self.analyze(node.children[0])

        # السماح BOOL -> INT
        if var_type == "INT" and expr_type == "BOOL":
            expr_type = "INT"

        if expr_type != var_type:
            raise Exception(
                f"Cannot assign {expr_type} to {var_type}"
            )

        expr_code = self.expr_to_cpp(node.children[0])

        self.emit(
            f"{node.value} = {expr_code};"
        )

    # PRINT........................................................

    def visit_PRINT(self, node):

        expr = self.expr_to_cpp(node.children[0])

        self.emit(
            f"cout << {expr} << endl;"
        )

    # INPUT..........................................................

    def visit_INPUT(self, node):

        self.symbols.lookup(node.value)

        self.emit(
            f"cin >> {node.value};"
        )

    # BLOCK..............................................................

    def visit_BLOCK(self, node):

        self.symbols.push()

        self.enter_scope()

        for child in node.children:
            self.analyze(child)

        self.exit_scope()

        self.symbols.pop()

    # IF................................................................

    def visit_IF(self, node):

        cond_type = self.analyze(node.children[0])

        if cond_type != "BOOL":
            raise Exception(
                "IF condition must be BOOL"
            )

        cond = self.expr_to_cpp(node.children[0])

        self.emit(f"if ({cond})")

        self.symbols.push()

        self.enter_scope()

        self.analyze(node.children[1])

        self.exit_scope()

        self.symbols.pop()

        # else
        if len(node.children) > 2:

            self.emit("else")

            self.symbols.push()

            self.enter_scope()

            self.analyze(node.children[2])

            self.exit_scope()

            self.symbols.pop()

    # WHILE.................................................................

    def visit_WHILE(self, node):

        cond_type = self.analyze(node.children[0])

        if cond_type != "BOOL":
            raise Exception(
                "WHILE condition must be BOOL"
            )

        cond = self.expr_to_cpp(node.children[0])

        self.emit(f"while ({cond})")

        self.symbols.push()

        self.enter_scope()

        self.analyze(node.children[1])

        self.exit_scope()

        self.symbols.pop()

    
    # FOR..................................................................

    def visit_FOR(self, node):

        self.symbols.push()

        init = self.for_stmt(node.children[0])

        cond = self.expr_to_cpp(node.children[1])

        update = self.for_stmt(node.children[2])

        self.emit(
            f"for ({init}; {cond}; {update})"
        )

        self.enter_scope()

        self.analyze(node.children[3])

        self.exit_scope()

        self.symbols.pop()

    # FOR HELPERS.................................................................

    def for_stmt(self, node):

        # declaration
        if node.type == "DECL":

            expr = self.expr_to_cpp(node.children[0])

            var_type = self.map_type(node.dtype)

            cpp_type = self.to_cpp_type(var_type)

            return (
                f"{cpp_type} {node.value} = {expr}"
            )

        # assignment
        elif node.type == "ASSIGN":

            expr = self.expr_to_cpp(node.children[0])

            return f"{node.value} = {expr}"

        raise Exception(
            f"Invalid FOR statement: {node.type}"
        )

    # EXPRESSIONS -> CPP......................................................

    def expr_to_cpp(self, node):

        if node is None:
            return ""

        if node.type == "INT":
            return str(int(node.value))

        if node.type == "FLOAT":
            return str(float(node.value))

        if node.type == "STRING":

            text = str(node.value)

            text = text.replace('"', '')

            return f"\"{text}\""

        if node.type == "BOOL":

            return "1" if node.value else "0"

        if node.type == "ID":
            return node.value

        if node.type == "BINOP":

            left = self.expr_to_cpp(
                node.children[0]
            )

            right = self.expr_to_cpp(
                node.children[1]
            )

            return (
                f"({left} {node.value} {right})"
            )

        if node.type == "UNARY":

            expr = self.expr_to_cpp(
                node.children[0]
            )

            return f"({node.value}{expr})"

        raise Exception(
            f"Unsupported expression type: {node.type}"
        )

    # BINOP SEMANTIC.....................................................

    def visit_BINOP(self, node):

        left = self.analyze(node.children[0])

        right = self.analyze(node.children[1])

        op = node.value

        if left == "BOOL":
            left = "INT"

        if right == "BOOL":
            right = "INT"

        if op in ["+", "-", "*", "/"]:

            if left not in ["INT", "FLOAT"]:
                raise Exception(
                    f"Left operand invalid: {left}"
                )

            if right not in ["INT", "FLOAT"]:
                raise Exception(
                    f"Right operand invalid: {right}"
                )

            if left == "FLOAT" or right == "FLOAT":
                return "FLOAT"

            return "INT"

        if op in [
            "<", ">",
            "<=", ">=",
            "==", "!="
        ]:

            return "BOOL"

        raise Exception(
            f"Unknown operator '{op}'"
        )

    # LITERALS.........................................................

    def visit_INT(self, node):
        return "INT"

    def visit_FLOAT(self, node):
        return "FLOAT"

    def visit_STRING(self, node):
        return "STRING"

    def visit_BOOL(self, node):
        return "BOOL"

    def visit_ID(self, node):
        return self.symbols.lookup(node.value)

    # PROGRAM GENERATION.......................................................

    def generate_program(self):

        code = []

        code.append("#include <iostream>")
        code.append("#include <string>")
        code.append("")
        code.append("using namespace std;")
        code.append("")
        code.append("int main()")
        code.append("{")

        code.extend(self.cpp_code)

        code.append("")
        code.append("    return 0;")
        code.append("}")

        return "\n".join(code)

    # WRITE CPP FILE.........................................................

    def write_cpp_file(
        self,
        filename="program.cpp"
    ):

        code = self.generate_program()

        with open(
            filename,
            "w",
            encoding="utf-8"
        ) as f:

            f.write(code)

        print(
            f"C++ file generated: {filename}"
        )

# analyzer = SemanticAnalyzer()
# analyzer.analyze(tree)

# analyzer.write_cpp_file("program.cpp")