from __future__ import unicode_literals

import ast
import operator as op

class Comparer(ast.NodeTransformer):

    operators = {
        ast.Add: op.add,
        ast.Sub: op.sub,
        ast.Mult: op.mul,
        ast.Div: op.truediv,
        ast.USub: op.neg,
    }

    def __init__(self, context):
        self.context = context

    def visit_Compare(self, node):
        self.generic_visit(node)
        left = node.left.n
        right = node.comparators[0].n

        self.equal = left == right
        self.diff = left - right

    def visit_BinOp(self, node):
        self.generic_visit(node)
        return ast.copy_location(
            ast.Num(self.operators[type(node.op)](node.left.n, node.right.n)),
            node
        )

    def visit_Name(self, node):
        return ast.copy_location(ast.Num(self.context[node.id]),
                                 node)

class ExprSolver(object):
    """
    Accepts a text expression defining a comparison ("a + b == x + y * 2"),
    transforms it so values can be used, and verifies the truth of the
    expression. If false, returns how much the expression is off by.
    """

    def __init__(self, expr, lookup_context):
        self.expr = expr
        self.context = lookup_context
        self.ast = ast.parse(expr)
        self.rendered = self._render(expr)
        self.diff = None

    def _render(self, expr):
        tokens = expr.split()
        rendered = []
        for tt in tokens:
            if tt in self.context:
                tt = '{}({})'.format(tt, self.context[tt])
            rendered.append(tt)
        return ' '.join(rendered)

    def verify(self):
        compare = self.ast.body[0].value
        assert isinstance(compare, ast.Compare)
        cc = Comparer(self.context)
        cc.visit(compare)
        self.diff = cc.diff
