"""Test cases for the type checker: exporting inferred types"""

import os.path
import re

import typing

from mypy import build
from mypy.myunit import Suite, run_test
from mypy.test import config
from mypy.test.data import parse_test_cases
from mypy.test.helpers import assert_string_arrays_equal
from mypy.util import short_type
from mypy.nodes import NameExpr, TypeVarExpr, CallExpr
from mypy.traverser import TraverserVisitor
from mypy.errors import CompileError


class TypeExportSuite(Suite):
    # List of files that contain test case descriptions.
    files = ['typexport-basic.test']

    def cases(self):
        c = []
        for f in self.files:
            c += parse_test_cases(os.path.join(config.test_data_prefix, f),
                                  self.run_test, config.test_temp_dir)
        return c

    def run_test(self, testcase):
        a = []
        try:
            line = testcase.input[0]
            mask = ''
            if line.startswith('##'):
                mask = '(' + line[2:].strip() + ')$'

            src = '\n'.join(testcase.input)
            result = build.build(program_path='main',
                                 target=build.TYPE_CHECK,
                                 program_text=src,
                                 flags=[build.TEST_BUILTINS],
                                 alt_lib_path=config.test_temp_dir)
            map = result.types
            nodes = map.keys()

            # Ignore NameExpr nodes of variables with explicit (trivial) types
            # to simplify output. Also ignore 'Undefined' nodes.
            searcher = VariableDefinitionNodeSearcher()
            for file in result.files.values():
                file.accept(searcher)
            ignored = searcher.nodes

            # Filter nodes that should be included in the output.
            keys = []
            for node in nodes:
                if node.line is not None and node.line != -1 and map[node]:
                    if ignore_node(node) or node in ignored:
                        continue
                    if (re.match(mask, short_type(node))
                            or (isinstance(node, NameExpr)
                                and re.match(mask, node.name))):
                        # Include node in output.
                        keys.append(node)

            for key in sorted(keys,
                              key=lambda n: (n.line, short_type(n),
                                             str(n) + str(map[n]))):
                ts = str(map[key]).replace('*', '')  # Remove erased tags
                ts = ts.replace('__main__.', '')
                a.append('{}({}) : {}'.format(short_type(key), key.line, ts))
        except CompileError as e:
            a = e.messages
        assert_string_arrays_equal(
            testcase.output, a,
            'Invalid type checker output ({}, line {})'.format(testcase.file,
                                                               testcase.line))


class VariableDefinitionNodeSearcher(TraverserVisitor):
    def __init__(self):
        self.nodes = set()

    def visit_assignment_stmt(self, s):
        if s.type or ignore_node(s.rvalue):
            for lvalue in s.lvalues:
                if isinstance(lvalue, NameExpr):
                    self.nodes.add(lvalue)
            if (isinstance(s.rvalue, NameExpr)
                    and s.rvalue.fullname == 'typing.Undefined'):
                self.nodes.add(s.rvalue)


def ignore_node(node):
    """Return True if node is to be omitted from test case output."""

    # We want to get rid of object() expressions in the typing module stub
    # and also TypeVar(...) expressions. Since detecting whether a node comes
    # from the typing module is not easy, we just to strip them all away.
    if isinstance(node, TypeVarExpr):
        return True
    if isinstance(node, NameExpr) and node.fullname == 'builtins.object':
        return True
    if isinstance(node, NameExpr) and node.fullname == 'builtins.None':
        return True
    if isinstance(node, CallExpr) and (ignore_node(node.callee) or
                                       node.analyzed):
        return True

    return False


if __name__ == '__main__':
    import sys
    run_test(TypeExportSuite(), sys.argv[1:])
