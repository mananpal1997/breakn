import inspect
import ast
import textwrap
import types
import typing
import sys

if sys.version_info < (3, 10):
    import typing_extensions

    P = typing_extensions.ParamSpec("P")
else:
    P = typing.ParamSpec("P")
R = typing.TypeVar("R")


class BreakNValidator(ast.NodeVisitor):
    """
    AST Visitor to validate the correct usage of the `breakn` function.

    It ensures:
    - The argument is a positive integer.
    - The argument does not exceed the enclosing loop depth.
    """

    def __init__(self) -> None:
        self.current_loop_depth = 0
        self.errors: typing.List[typing.Tuple[int, str]] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        original_depth = self.current_loop_depth
        self.current_loop_depth = 0
        self.generic_visit(node)
        self.current_loop_depth = original_depth

    def visit_For(self, node: ast.For) -> None:
        self.current_loop_depth += 1
        self.generic_visit(node)
        self.current_loop_depth -= 1

    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Name) and node.func.id == "breakn":
            if len(node.args) != 1:
                self.errors.append(
                    (node.lineno, "breakn() requires exactly one argument")
                )
            else:
                arg = node.args[0]
                if not isinstance(arg, ast.Constant) or not isinstance(arg.value, int):
                    self.errors.append(
                        (node.lineno, "breakn() argument must be an integer literal")
                    )
                else:
                    x = arg.value
                    if x <= 0:
                        self.errors.append(
                            (node.lineno, "breakn() argument must be positive")
                        )
                    elif x > self.current_loop_depth:
                        self.errors.append(
                            (
                                node.lineno,
                                f"breakn({x}) exceeds enclosing {self.current_loop_depth} loops",
                            )
                        )
        self.generic_visit(node)


def breaker(func: typing.Callable[P, R]) -> typing.Callable[P, R]:
    source = inspect.getsource(func)
    tree = ast.parse(textwrap.dedent(source))

    func_def = typing.cast(ast.FunctionDef, tree.body[0])
    func_def.decorator_list = []

    validator = BreakNValidator()
    validator.visit(tree)

    if validator.errors:
        function_start_line = func.__code__.co_firstlineno
        func_def_lineno = func_def.lineno
        lineno, msg = validator.errors[0]
        adjusted_lineno = function_start_line + (lineno - func_def_lineno)
        raise SyntaxError(msg, (func.__code__.co_filename, adjusted_lineno, 0, None))

    breakn_exception_class = ast.ClassDef(
        name="BreakNException",
        bases=[ast.Name(id="Exception", ctx=ast.Load())],
        keywords=[],
        body=[
            ast.FunctionDef(
                name="__init__",
                args=ast.arguments(
                    posonlyargs=[],
                    args=[ast.arg(arg="self"), ast.arg(arg="count")],
                    kwonlyargs=[],
                    kw_defaults=[],
                    defaults=[],
                ),
                body=[
                    ast.Expr(
                        ast.Call(
                            func=ast.Attribute(
                                value=ast.Name(id="Exception", ctx=ast.Load()),
                                attr="__init__",
                                ctx=ast.Load(),
                            ),
                            args=[
                                ast.Name(id="self", ctx=ast.Load()),
                                ast.Constant(value="BreakNException"),
                            ],
                            keywords=[],
                        )
                    ),
                    ast.Assign(
                        targets=[
                            ast.Attribute(
                                value=ast.Name(id="self", ctx=ast.Load()),
                                attr="count",
                                ctx=ast.Store(),
                            )
                        ],
                        value=ast.Name(id="count", ctx=ast.Load()),
                    ),
                ],
                decorator_list=[],
                returns=None,
            )
        ],
        decorator_list=[],
    )

    breakn_function = ast.FunctionDef(
        name="breakn",
        args=ast.arguments(
            posonlyargs=[],
            args=[ast.arg(arg="x")],
            kwonlyargs=[],
            kw_defaults=[],
            defaults=[],
        ),
        body=[
            ast.Raise(
                exc=ast.Call(
                    func=ast.Name(id="BreakNException", ctx=ast.Load()),
                    args=[ast.Name(id="x", ctx=ast.Load())],
                    keywords=[],
                ),
                cause=None,
            )
        ],
        decorator_list=[],
        returns=None,
    )

    func_def.body.insert(0, breakn_exception_class)
    func_def.body.insert(1, breakn_function)

    class ForLoopTransformer(ast.NodeTransformer):
        def visit_For(self, node: ast.AST) -> ast.For:
            node = self.generic_visit(node)

            handler_body: typing.List[ast.stmt] = [
                ast.If(
                    test=ast.Compare(
                        left=ast.Attribute(
                            value=ast.Name(id="e", ctx=ast.Load()),
                            attr="count",
                            ctx=ast.Load(),
                        ),
                        ops=[ast.Eq()],
                        comparators=[ast.Constant(value=1)],
                    ),
                    body=[ast.Break()],
                    orelse=[
                        ast.AugAssign(
                            target=ast.Attribute(
                                value=ast.Name(id="e", ctx=ast.Load()),
                                attr="count",
                                ctx=ast.Store(),
                            ),
                            op=ast.Sub(),
                            value=ast.Constant(value=1),
                        ),
                        ast.Raise(exc=ast.Name(id="e", ctx=ast.Load()), cause=None),
                    ],
                )
            ]
            handler = ast.ExceptHandler(
                type=ast.Name(id="BreakNException", ctx=ast.Load()),
                name="e",
                body=handler_body,
            )

            node = typing.cast(ast.For, node)
            try_node = ast.Try(
                body=node.body, handlers=[handler], orelse=[], finalbody=[]
            )

            new_for = ast.For(
                target=node.target,
                iter=node.iter,
                body=[try_node],
                orelse=node.orelse,
                type_comment=node.type_comment,
            )

            return new_for

    transformer = ForLoopTransformer()
    new_tree = transformer.visit(tree)
    ast.fix_missing_locations(new_tree)

    module = types.ModuleType("modified_module")
    exec(compile(new_tree, filename="<ast>", mode="exec"), module.__dict__)
    new_func = getattr(module, func.__name__)

    return typing.cast(typing.Callable[P, R], new_func)
