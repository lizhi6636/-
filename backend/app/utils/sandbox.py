"""Restricted execution environment for user-submitted strategy code."""

import ast
from typing import Set

# Allowed built-in functions
ALLOWED_BUILTINS: Set[str] = {
    'abs', 'all', 'any', 'bool', 'dict', 'divmod', 'enumerate',
    'filter', 'float', 'int', 'isinstance', 'issubclass',
    'len', 'list', 'map', 'max', 'min', 'pow', 'print',
    'range', 'repr', 'reversed', 'round', 'set', 'slice',
    'sorted', 'str', 'sum', 'tuple', 'type', 'zip',
    'True', 'False', 'None', 'Exception', 'ValueError', 'TypeError',
    'AttributeError', 'KeyError', 'IndexError', 'StopIteration',
    'NotImplementedError', 'ArithmeticError', 'ZeroDivisionError',
}

# Allowed import modules
ALLOWED_IMPORTS: Set[str] = {
    'backtrader', 'numpy', 'pandas', 'datetime', 'math',
    'statistics', 'collections', 'itertools', 'functools',
    'operator', 'decimal', 'fractions', 'random',
}


class SandboxError(Exception):
    """Raised when user code fails sandbox validation."""
    pass


class ImportValidator(ast.NodeVisitor):
    """AST visitor that validates all imports against the allowlist."""

    def __init__(self):
        self.errors: list[str] = []

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            if alias.name not in ALLOWED_IMPORTS:
                self.errors.append(f"不允许导入模块: {alias.name}")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.module and node.module not in ALLOWED_IMPORTS:
            self.errors.append(f"不允许导入模块: {node.module}")
        self.generic_visit(node)


def validate_strategy_code(code: str) -> tuple[bool, list[str]]:
    """Validate user strategy code for security.

    Returns (is_valid, list_of_errors).
    """
    errors = []

    # Check syntax
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return False, [f"语法错误: {e}"]

    # Check imports
    validator = ImportValidator()
    validator.visit(tree)
    if validator.errors:
        return False, validator.errors

    # Check for forbidden builtins usage
    forbidden_calls = {'open', '__import__', 'eval', 'exec', 'compile',
                       'globals', 'locals', 'getattr', 'setattr', 'delattr',
                       'breakpoint', '__builtins__'}
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id in forbidden_calls:
            errors.append(f"不允许使用: {node.id}")

    if errors:
        return False, errors

    return True, []


def get_restricted_builtins() -> dict:
    """Get a restricted builtins dict for sandbox execution."""
    import builtins
    return {
        name: getattr(builtins, name)
        for name in ALLOWED_BUILTINS
        if hasattr(builtins, name)
    }


def execute_strategy(code: str, context: dict) -> dict:
    """Execute strategy code in a restricted environment.

    Args:
        code: Python strategy code
        context: Variables to pass into the execution context

    Returns:
        dict of results extracted from the execution context
    """
    # Validate first
    is_valid, errors = validate_strategy_code(code)
    if not is_valid:
        raise SandboxError(f"代码验证失败: {'; '.join(errors)}")

    restricted_builtins = get_restricted_builtins()
    exec_globals = {"__builtins__": restricted_builtins}
    exec_globals.update(context)

    exec_locals = {}
    exec(code, exec_globals, exec_locals)

    return exec_locals
