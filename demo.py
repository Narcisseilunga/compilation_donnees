from lark import Lark, Visitor, Tree, Token

grammar = """
    start: "debut" instruction* "fin"
    
    instruction: declaration
               | affectation
               | lecture
               | affichage
               | conditionnelle
               | repetitif
               | fonction
               | retour

    declaration: "declare" IDENTIFIER
    affectation: IDENTIFIER "=" expression
    lecture: "lire" IDENTIFIER
    affichage: "afficher" (IDENTIFIER | STRING)
    conditionnelle: "si" condition "alors" instruction* ("sinon" instruction*)? "fin si"
    repetitif: "pour" IDENTIFIER "de" INT "a" INT "faire" instruction* "fin pour"
              | "tant que" condition "faire" instruction* "fin tant que"
              | "répéter" instruction* "jusqu'à" condition "fin répéter"
    fonction: "fonction" IDENTIFIER "(" param_list? ")" instruction* "fin fonction"
    retour: "retourner" expression

    param_list: IDENTIFIER ("," IDENTIFIER)*

    condition: expression ("==" | "!=" | "<" | "<=" | ">" | ">=") expression
    expression: appel_fonction
              | IDENTIFIER
              | INT
              | STRING
              | "(" expression ")"
              | expression ("+" | "-" | "*" | "/") expression

    appel_fonction: IDENTIFIER "(" (expression ("," expression)*)? ")"

    %import common.INT
    %import common.CNAME -> IDENTIFIER
    STRING: /"([^"\\\\]|\\\\.)*"/
    %import common.WS
    %ignore WS
"""
class Evaluator(Visitor):
    def __init__(self):
        self.variables = {}
        self.functions = {}
        self.result = None

    def declaration(self, tree):
        variable = tree.children[0].value
        self.variables[variable] = None

    def affectation(self, tree):
        variable = tree.children[0].value
        value = self.evaluate(tree.children[1])
        self.variables[variable] = value

    def lecture(self, tree):
        variable = tree.children[0].value
        self.variables[variable] = int(input(f"Entrez la valeur pour {variable}: "))

    def affichage(self, tree):
        element = tree.children[0]
        if isinstance(element, Token) and element.type == "IDENTIFIER":
            variable = element.value
            if variable in self.variables and self.variables[variable] is not None:
                print(self.variables[variable])
            else:
                raise ValueError(f"La variable '{variable}' a été utilisée dans 'afficher' sans avoir reçu de valeur.")
        else:
            print(element.value)

    def conditionnelle(self, tree):
        condition = self.evaluate(tree.children[0])
        if condition:
            for instruction in tree.children[2:]:
                self.visit(instruction)
        elif len(tree.children) > 3:
            for instruction in tree.children[3:]:
                self.visit(instruction)

    def repetitif(self, tree):
        var_name = tree.children[0].value
        start = int(tree.children[1].value)
        end = int(tree.children[2].value)
        for i in range(start, end + 1):
            self.variables[var_name] = i
            for instruction in tree.children[4:]:
                self.visit(instruction)

    def fonction(self, tree):
        function_name = tree.children[0].value
        param_names = [child.value for child in tree.children[1].children]
        instructions = tree.children[-1]
        self.functions[function_name] = (param_names, instructions)

    def appel_fonction(self, tree):
        function_name = tree.children[0].value
        args = [self.evaluate(arg) for arg in tree.children[1:]]
        param_names, instructions = self.functions[function_name]
        local_vars = dict(zip(param_names, args))
        previous_vars = self.variables.copy()
        self.variables.update(local_vars)
        for instruction in instructions.children:
            self.visit(instruction)
        result = self.result
        self.variables = previous_vars
        return result

    def retour(self, tree):
        self.result = self.evaluate(tree.children[0])

    def evaluate(self, tree):
        if isinstance(tree, Token):
            if tree.type == "INT":
                return int(tree.value)
            elif tree.type == "IDENTIFIER":
                if tree.value in self.variables:
                    value = self.variables[tree.value]
                    if value is None:
                        raise ValueError(f"La variable '{tree.value}' a été déclarée mais n'a pas reçu de valeur.")
                    return value
                else:
                    raise ValueError(f"La variable '{tree.value}' a été utilisée sans être déclarée.")
        elif tree.data == "expression":
            left = self.evaluate(tree.children[0])
            if len(tree.children) == 1:
                return left
            op = tree.children[1].value
            right = self.evaluate(tree.children[2])
            if op == "+":
                return left + right
            elif op == "-":
                return left - right
            elif op == "*":
                return left * right
            elif op == "/":
                return left / right
        elif tree.data == "appel_fonction":
            return self.visit(tree)
parser = Lark(grammar)

def analyze_code(file_path):
    with open(file_path, 'r') as file:
        code = file.read()

    try:
        tree = parser.parse(code)
        evaluator = Evaluator()
        evaluator.visit(tree)
        print("Le code est valide.")
    except Exception as e:
        print(f"Erreur de syntaxe : {e}")

if __name__ == "__main__":
    analyze_code('test.pseudocode')
