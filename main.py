from antlr4 import *
from yaplLexer import yaplLexer
from yaplParser import yaplParser
from yaplListener import yaplListener
from antlr4.tree.Trees import Trees
from antlr4.error.ErrorListener import ErrorListener
from yaplVisitor import yaplVisitor
from graphviz import Digraph
import os
import pprint
import re


def visualize_tree(tree, filename):
    graph = Digraph(comment='YAPL Syntax Tree')
    build_graph(tree, graph)
    graph.render(filename, view=True)


def build_graph(tree, graph, parent=None):
    if tree.getText():
        node = str(hash(tree))
        graph.node(node, tree.getText())
        if parent:
            graph.edge(parent, node)
        for i in range(tree.getChildCount()):
            build_graph(tree.getChild(i), graph, node)


class CustomErrorListener(ErrorListener):
    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        # Personalizar el mensaje de error para el análisis sintáctico
        print(f"\nERROR sintáctico en línea {line}, columna {column}: {msg}\n")

    def reportError(self, recognizer, e):
        # Personalizar el mensaje de error para el análisis léxico
        token = recognizer.getCurrentToken()
        line = token.line
        column = token.column
        print(
            f"\nERROR léxico en línea {line}, columna {column}: Carácter inesperado '{token.text}'\n")


class yaplListener(ParseTreeListener):
    def enterExpression(self, ctx: yaplParser.ExpressionContext):
        print("Entrando en expresión:", ctx.getText())

    def exitExpression(self, ctx: yaplParser.ExpressionContext):
        print("Saliendo de expresión:", ctx.getText())


class SymbolTable:
    def __init__(self):
        self.scopes = [{}]
        self.byte_count = 0
        self.total_byte_count = 0

    def enter_scope(self):
        self.scopes.append({})

    def exit_scope(self):
        self.scopes.pop()

    def declare(self, symbol, type):
        self.scopes[-1][symbol] = {'type': type}
        if type == "int" or type == "string":
            self.byte_count = 4
        elif type == "float":
            self.byte_count = 8
        elif type == "bool":
            self.byte_count = 1
        elif type.startswith("method:"):
            self.byte_count = 0
            if type.endswith("int") or type.endswith("string"):
                self.byte_count = 4
        else:  # Para el caso de 'class' y cualquier otro tipo no especificado
            self.byte_count = 0

        self.scopes[-1][symbol]['byte_count'] = self.byte_count
        self.total_byte_count += self.byte_count
        self.scopes[0]['Main']['total_byte_count'] = self.total_byte_count

    def lookup(self, symbol):
        for scope in reversed(self.scopes):
            if symbol in scope:
                return scope[symbol]
        return None


class MyListener(yaplListener):
    def __init__(self):
        self.symbol_table = SymbolTable()

    def enterClassDeclaration(self, ctx: yaplParser.ClassDeclarationContext):
        print("Entrando en ClassDeclaration")
        class_name = ctx.TYPE_ID()[0].getText()
        self.symbol_table.declare(class_name, "class")
        self.symbol_table.enter_scope()  # Nuevo ámbito para la clase

    def exitClassDeclaration(self, ctx: yaplParser.ClassDeclarationContext):
        print("Saliendo de ClassDeclaration")
        # self.symbol_table.exit_scope()  # Salir del ámbito de la clase

    def enterMethodDeclaration(self, ctx: yaplParser.MethodDeclarationContext):
        print("Entrando en MethodDeclaration")
        method_name = ctx.ID().getText()
        # Esto devuelve el texto del tipo
        method_type = ctx.getChild(0).getText()
        self.symbol_table.declare(method_name, "method: " + method_type)
        self.symbol_table.enter_scope()  # Nuevo ámbito para el método

    def exitMethodDeclaration(self, ctx: yaplParser.MethodDeclarationContext):
        print("Saliendo de MethodDeclaration")
        # self.symbol_table.exit_scope()  # Salir del ámbito del método

    def enterBlock(self, ctx: yaplParser.BlockContext):
        print("Entrando en Block")
        # self.symbol_table.enter_scope()  # Nuevo ámbito para el bloque

    def exitBlock(self, ctx: yaplParser.BlockContext):
        print("Saliendo de Block")
        # self.symbol_table.exit_scope()  # Salir del ámbito del bloque

    def enterAttributeDeclaration(self, ctx: yaplParser.AttributeDeclarationContext):
        print("Entrando en AttributeDeclaration")
        symbol = ctx.ID().getText()
        # Esto devuelve el primer hijo, que debe ser el contexto de 'type'
        type_ctx = ctx.getChild(0)
        type_text = type_ctx.getText()  # Esto devuelve el texto del tipo
        self.symbol_table.declare(symbol, type_text)

    def enterVariableDeclaration(self, ctx: yaplParser.VariableDeclarationContext):
        print("Entrando en VariableDeclaration")
        symbol = ctx.ID().getText()
        # print("symbol: ", symbol)
        # Esto devuelve el primer hijo, que debe ser el contexto de 'type'
        type_ctx = ctx.getChild(0)
        type_text = type_ctx.getText()
        # print("type_text: ", type_text)
        self.symbol_table.declare(symbol, type_text)


class MyVisitor(yaplVisitor):
    def __init__(self):
        self.code = {}
        self.class_name = ""
        self.method_name = ""
        self.cuadruplos = []
        self.temp_count = 0
        self.call = False

    def new_temp(self):
        # Función para generar un nuevo nombre de variable temporal
        self.temp_count += 1
        return f"t{self.temp_count}"

    def visitProgram(self, ctx: yaplParser.ProgramContext):
        print("Entrando en Program")
        return self.visitChildren(ctx)

    def visitClassDeclaration(self, ctx: yaplParser.ClassDeclarationContext):
        # print("visitClassDeclaration")
        self.class_name = ctx.TYPE_ID()[0].getText()
        self.method_name = ""
        # print(self.class_name)
        self.code[self.class_name] = []
        self.code[self.class_name].append("BeginFuc_")
        self.visitChildren(ctx)
        self.code[self.class_name].append("EndFunc_")

    def visitMethodDeclaration(self, ctx: yaplParser.MethodDeclarationContext):
        print("visitMethodDeclaration")
        if self.method_name != "":
            self.method_name = ""
        self.method_name = ctx.ID().getText()
        # print(self.method_name)
        self.code[self.class_name].append(
            {f"{self.class_name}.{self.method_name}:": []})
        self.code[self.class_name][-1][f"{self.class_name}.{self.method_name}:"].append(
            "BeginFuc_")
        self.visitChildren(ctx)
        self.code[self.class_name][-1][f"{self.class_name}.{self.method_name}:"].append(
            "EndFunc_")
        self.method_name = ""

    def visitMethodCallStatement(self, ctx: yaplParser.MethodCallStatementContext):
        print("visitMethodCallStatement")
        print(ctx.getText())
        method_name = ctx.ID().getText()
        if self.method_name:
            target_code = self.code[self.class_name][-1][f"{self.class_name}.{self.method_name}:"]
        else:
            target_code = self.code[self.class_name]

        if ctx.expressionList():
            for expression in ctx.expressionList().expression():
                temp = self.new_temp()
                self.cuadruplos.append(
                    ('PARAM', expression.getText(), '-', temp))
                target_code.append(
                    f"{temp} = {expression.getText()}")
                target_code.append(
                    f"PUSHPARAM {temp}")
                self.cuadruplos.append(
                    ('PUSHPARAM', temp, '-', '-'))
            self.cuadruplos.append(('CALL', method_name, '-', '-'))

        if self.call:
            self.call = False
            return f"LCall {method_name}()"
        else:
            target_code.append(
                f"LCall {method_name}()")

    def visitBlock(self, ctx: yaplParser.BlockContext):
        print("Entrando en Block")
        return self.visitChildren(ctx)

    def visitAttributeDeclaration(self, ctx: yaplParser.AttributeDeclarationContext):
        print("visitAttributeDeclaration")
        var_name = ctx.ID().getText()
        print(var_name)
        if ctx.ID():
            expression_result = ctx.type_().getText()
            self.code[self.class_name].append(
                f"{var_name} = {expression_result}")

            self.cuadruplos.append(
                ('ASSIGN', expression_result, '-', var_name))

    def visitAssignmentDeclaration(self, ctx: yaplParser.AssignmentDeclarationContext):
        print("visitAssignmentDeclaration")
        var_name = ctx.ID().getText()
        expression_result = ctx.expression().getText()
        children = self.visit(ctx.expression())
        print(children)

        if children:
            self.code[self.class_name].append(
                f"{var_name} = {children}")

            self.cuadruplos.append(
                ('ASSIGN', children, '-', var_name))
        else:
            self.code[self.class_name].append(
                f"{var_name} = {expression_result}")
            self.cuadruplos.append(('<-', expression_result, '-', var_name))

    def visitVariableDeclaration(self, ctx: yaplParser.VariableDeclarationContext):
        print("visitVariableDeclaration")
        print(ctx.getText())
        var_name = ctx.ID().getText()
        print(var_name)
        expression_result = ctx.type_().getText()
        if self.method_name:
            target_code = self.code[self.class_name][-1][f"{self.class_name}.{self.method_name}:"]
        else:
            target_code = self.code[self.class_name]

        if ctx.statement():
            target_code.append(
                f"{var_name} = {expression_result}")
            self.cuadruplos.append(
                ('ASSIGN', expression_result, '-', var_name))
            if re.search(r'[\+\-\*\/]', ctx.statement().getText()) or re.search(r'[(]', ctx.statement().getText()):
                self.call = True
                res = self.visit(ctx.statement())
            else:
                res = ctx.statement().getText()
            target_code.append(
                f"{var_name} = {res}")
            self.cuadruplos.append(
                ('<-', var_name, '-', res))
        else:
            target_code.append(
                f"{var_name} = {expression_result}")
            self.cuadruplos.append(
                ('ASSIGN', expression_result, '-', var_name))

    def visitExpression(self, ctx: yaplParser.ExpressionContext):
        print("Entrando en Expression")
        return self.visitChildren(ctx)

    def visitAdditionExpression(self, ctx: yaplParser.AdditionExpressionContext):
        print("visitAdditionExpression")
        print(ctx.getText())
        left = self.visit(ctx.expression(0)) or ctx.expression(0).getText()
        right = self.visit(ctx.expression(1)) or ctx.expression(1).getText()
        temp = self.new_temp()

        self.cuadruplos.append(('add', temp, left, right))

        if self.method_name:
            target_code = self.code[self.class_name][-1][f"{self.class_name}.{self.method_name}:"]
        else:
            target_code = self.code[self.class_name]

        target_code.append(f"{temp} = {left} + {right}")
        return temp

    def visitSubtractionExpression(self, ctx: yaplParser.SubtractionExpressionContext):
        print("visitSubtractionExpression")
        print(ctx.getText())
        left = self.visit(ctx.expression(0)) or ctx.expression(0).getText()
        right = self.visit(ctx.expression(1)) or ctx.expression(1).getText()
        temp = self.new_temp()

        self.cuadruplos.append(('-', left, right, temp))

        if self.method_name:
            target_code = self.code[self.class_name][-1][f"{self.class_name}.{self.method_name}:"]
        else:
            target_code = self.code[self.class_name]

        target_code.append(f"{temp} = {left} - {right}")
        return temp

    def visitMultiplicationExpression(self, ctx: yaplParser.MultiplicationExpressionContext):
        print("visitMultiplicationExpression")
        print(ctx.getText())
        left = self.visit(ctx.expression(0)) or ctx.expression(0).getText()
        right = self.visit(ctx.expression(1)) or ctx.expression(1).getText()
        temp = self.new_temp()

        self.cuadruplos.append(('*', left, right, temp))

        if self.method_name:
            target_code = self.code[self.class_name][-1][f"{self.class_name}.{self.method_name}:"]
        else:
            target_code = self.code[self.class_name]

        target_code.append(f"{temp} = {left} * {right}")
        return temp

    def visitDivisionExpression(self, ctx: yaplParser.DivisionExpressionContext):
        print("visitDivisionExpression")
        print(ctx.getText())
        left = self.visit(ctx.expression(0)) or ctx.expression(0).getText()
        right = self.visit(ctx.expression(1)) or ctx.expression(1).getText()
        temp = self.new_temp()

        self.cuadruplos.append(('/', left, right, temp))

        if self.method_name:
            target_code = self.code[self.class_name][-1][f"{self.class_name}.{self.method_name}:"]
        else:
            target_code = self.code[self.class_name]

        target_code.append(f"{temp} = {left} / {right}")
        return temp


def main():
    # Lee el código fuente de YAPL desde un archivo o un string
    # input_stream = FileStream("codigo.yapl")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, 'codigo.yapl')
    with open(file_path, 'r', encoding='utf-8') as file:
        input_text = file.read()
    # with open("codigo.yapl", "r", encoding="utf-8") as file:
    #     input_text = file.read()
    input_stream = InputStream(input_text)

    lexer = yaplLexer(input_stream)
    stream = CommonTokenStream(lexer)
    parser = yaplParser(stream)

    # Asignar el manejador de errores personalizado al analizador léxico y sintáctico
    lexer.removeErrorListeners()
    lexer.addErrorListener(CustomErrorListener())
    parser = yaplParser(stream)
    parser.removeErrorListeners()
    parser.addErrorListener(CustomErrorListener())

    # tree = parser.expression()
    tree = parser.program()

    # Visualizar el árbol de análisis sintáctico en consola
    print('Arbol de analisis sintactico: ',
          Trees.toStringTree(tree, recog=parser), "\n")

    # Crear el árbol de análisis
    # yl = yaplListener()
    # walker = ParseTreeWalker()
    # walker.walk(yl, tree)

    myVisitor = MyVisitor()
    result = myVisitor.visit(tree)

    # crear tabla de simbolos
    my_listener = MyListener()
    walker = ParseTreeWalker()
    walker.walk(my_listener, tree)
    data = pprint.pformat(my_listener.symbol_table.scopes)
    print("\nTabla de Simbolos: \n", data)

    print("\nCódigo intermedio: \n")
    for key, value in myVisitor.code.items():
        print(key, ":", value)

    print("\nCuadruplos: \n")
    for cuadruplo in myVisitor.cuadruplos:
        print(cuadruplo)

    # visualize_tree(tree, "arbol_sintactico.pdf")


if __name__ == '__main__':
    main()
