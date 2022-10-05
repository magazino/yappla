import ast
from typing import Union

from simpleeval import SimpleEval, simple_eval


class PriorityQueue:
    """Very simple priority queue"""

    def __init__(self):
        self.queue = []

    def push(self, item, value):
        self.queue.append([item, value])
        self.queue.sort(key=lambda x: x[1])

    def pop(self):
        return self.queue.pop(0)

    def get_value(self, item):
        return [v[1] for v in self.queue if v[0] == item][0]

    def update_value(self, item, value):
        for s in self.queue:
            if s[0] == item:
                s[1] = value
                break

    def __contains__(self, item):
        return item in (x[0] for x in self.queue)

    def empty(self):
        return len(self.queue) == 0

    def __repr__(self):
        return "PRIORITY QUEUE {\n" + "\n".join(str((i, c)) for i, c in self.queue) + "\n}"


class bc:
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    ORANGE = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    ORANGE_BACKGROUND = "\033[43m"
    CYAN_BACKGROUND = "\033[46m"
    RED_BACKGROUND = "\033[41m"
    GREEN_BACKGROUND = "\033[42m"
    BLACK = "\033[30m"
    ENDC = "\033[0m"


class CompiledExpression(SimpleEval):
    def __init__(self, expr, operators=None, functions=None, names=None):
        super().__init__(operators=operators, functions=functions, names=names)
        expr = expr.replace("\n", " ")
        try:
            self.compiled_ast_tree = ast.parse(expr.strip()).body[0].value
        except Exception as exc:
            raise Exception("Cannot parse expression '%s': %s" % (expr.strip(), exc))
        self.expression = expr

    def eval_in_state(self, state: "State") -> bool:
        self.names = state
        return self._eval(self.compiled_ast_tree)

    def __repr__(self) -> str:
        return "COMPILED EXPRESSION {" + self.expression + "}"


def eval_expression(expression: Union[str, CompiledExpression], state: "State") -> bool:
    """Evaluate the given boolean expression in a state.

    The given expression can be either a string or an already CompiledExpression,
    this function will evaluate it given the variable assignment specified in the state.
    """
    if isinstance(expression, str):
        return simple_eval(expression, names=state)
    elif isinstance(expression, CompiledExpression):
        return expression.eval_in_state(state)
    else:
        return None


def diff_dicts(a, b, missing=KeyError):
    """
    From: https://stackoverflow.com/questions/32815640/how-to-get-the-difference-between-two-dictionaries-in-python
    Find keys and values which differ from `a` to `b` as a dict.

    If a value differs from `a` to `b` then the value in the returned dict will
    be: `(a_value, b_value)`. If either is missing then the token from 
    `missing` will be used instead.

    :param a: The from dict
    :param b: The to dict
    :param missing: A token used to indicate the dict did not include this key
    :return: A dict of keys to tuples with the matching value from a and b
    """
    return {
        key: (a.get(key, missing), b.get(key, missing))
        for key in dict(
            set(a.items()) ^ set(b.items())
        ).keys()
    }

