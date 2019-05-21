# Copyright 2017 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Converts Python unittest and mock assertions to PyTruth.

Usage:
  python convert.py file1.py [file2.py [...]]

Limitations:
  - Requires that the input be a compilable (hopefully passing) test.
  - The import of the truth module or AssertThat is not added.
  - Conversions may cause lines to increase in length.
  - Conversions may modify indentation and line wrapping.
  - Converts all instance of assertTrue(a) to AssertThat(a).IsTrue().
    In unittest, assertTrue() asserts *truthiness*, while PyTruth's IsTrue()
    matches only True itself. You may need to modify some IsTrue() assertions
    to IsTruthy(), and likewise for assertFalse(), IsFalse(), and IsFalsy().
  - Converts assertEqual(len(str), n) to AssertThat(str).HasSize(n).
    This works, but HasLength(n) is actually more appropriate.
  - Does not convert assertAlmostEqual(a, b, [places=p|delta=d]) to
    AssertThat(a).IsWithin(d).Of(b), and likewise for assertNotAlmostEqual().
  - Converts assertIn(k, dict) to AssertThat(k).IsIn(dict).
    This works, but AssertThat(dict).ContainsKey(k) is more appropriate.
  - Converts assertIn(s, str) to AssertThat(s).IsIn(str).
    This works, but AssertThat(str).Contains(s) is more appropriate.
  - Does not convert assertTrue(a == b) to AssertThat(a).IsEqualTo(b).
  - Does not convert assertTrue(not a) to AssertThat(a).IsFalse().
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import re

from absl import app
from absl import flags
from absl import logging


FLAGS = flags.FLAGS


class Converter(object):
  """Converts a list of files to PyTruth."""

  UNITTEST_ASSERTIONS = {
      'Equal': '({0}).IsEqualTo({1})',
      'Equals': '({0}).IsEqualTo({1})',
      'NotEqual': '({0}).IsNotEqualTo({1})',
      'NotEquals': '({0}).IsNotEqualTo({1})',
      'Empty': '({0}).IsEmpty()',
      'NotEmpty': '({0}).IsNotEmpty()',
      'Len': '({0}).HasSize({1})',
      'DictContainsSubset': '({0}.items()).ContainsAllIn({1}.items())',
      'DictEqual': '({0}).ContainsExactlyItemsIn({1})',
      'ListEqual': '({0}).ContainsExactlyElementsIn({1}).InOrder()',
      'SequenceEqual': '({0}).ContainsExactlyElementsIn({1}).InOrder()',
      'SetEqual': '({0}).ContainsExactlyElementsIn({1})',
      'TupleEqual': '({0}).ContainsExactlyElementsIn({1}).InOrder()',
      'SameElements': '({0}).ContainsExactlyElementsIn({1})',
      'CountEqual': ('(sorted({0})).ContainsExactlyElementsIn(sorted({1}))'
                     '.InOrder()'),
      'ItemsEqual': ('(sorted({0})).ContainsExactlyElementsIn(sorted({1}))'
                     '.InOrder()'),
      '_': '({0}).IsTrue()',
      'True': '({0}).IsTrue()',
      'False': '({0}).IsFalse()',
      'Less': '({0}).IsLessThan({1})',
      'LessEqual': '({0}).IsAtMost({1})',
      'Greater': '({0}).IsGreaterThan({1})',
      'GreaterEqual': '({0}).IsAtLeast({1})',
      'Is': '({0}).IsSameAs({1})',
      'IsNot': '({0}).IsNotSameAs({1})',
      'IsNone': '({0}).IsNone()',
      'IsNotNone': '({0}).IsNotNone()',
      'IsInstance': '({0}).IsInstanceOf({1})',
      'NotIsInstance': '({0}).IsNotInstanceOf({1})',
      'In': '({0}).IsIn({1})',
      'NotIn': '({0}).IsNotIn({1})',
      'Regex': '({0}).ContainsMatch({1})',
      'RegexpMatches': '({0}).ContainsMatch({1})',
      'NotRegex': '({0}).DoesNotContainMatch({1})',
      'NotRegexpMatches': '({0}).DoesNotContainMatch({1})',
      'Raises': '({0}).IsRaised()',
      'RaisesRegexp': '({0}).IsRaised(matching={1})',
      'RaisesWithRegexpMatch': '({0}).IsRaised(matching={1})',
  }

  INEQUALITY_REVERSALS = {
      'Less': '({0}).IsGreaterThan({1})',
      'LessEqual': '({0}).IsAtLeast({1})',
      'Greater': '({0}).IsLessThan({1})',
      'GreaterEqual': '({0}).IsAtMost({1})',
  }

  MEMBERSHIP_ASSERTIONS = frozenset((
      'CountEqual', 'ItemsEqual', 'SameElements'))

  REVERSIBLE_ASSERTIONS = frozenset(
      set(INEQUALITY_REVERSALS)
      | {k for k in UNITTEST_ASSERTIONS if 'Equal' in k}
      | MEMBERSHIP_ASSERTIONS)

  ASSERTION_RE = re.compile(
      r'(?P<assertion>(?P<indent>[ \t]*)self\.assert(?P<akey>{0})\s*\()'.format(
          r'|'.join(UNITTEST_ASSERTIONS)))

  MOCK_METHOD_ASSERTIONS = {
      'called': '({0}).WasCalled()',
      'not_called': '({0}).WasNotCalled()',
      'called_once': '({0}).WasCalled().Once()',
      'called_with': '({0}).WasCalled().LastWith({1})',
      'called_once_with': '({0}).WasCalled().Once().With({1})',
      'has_calls': '({0}).HasCalls({1}){2}',
      'any_call': '({0}).WasCalled().With({1})',
  }

  MOCK_METHOD_CALL_RE = re.compile(
      r'(?P<assertion>(?P<indent>[ \t]*)(?P<method>[\w.]+)\.'
      r'assert_(?P<akey>{0})\s*\()'.format(
          r'|'.join(MOCK_METHOD_ASSERTIONS)))

  ANY_ORDER_RE = re.compile(r'any_order\s*=\s*(.+)')

  EMPTY_CONTAINERS = frozenset((
      "''", '""', "r''", 'r""', "u''", 'u""',
      '()', '[]', '{}', 'dict()', 'frozenset()', 'list()', 'set()', 'tuple()',
      'collections.OrderedDict()'))

  LIST_EQUALITY_ASSERTIONS = frozenset((
      'Equal', 'Equals', 'ListEqual', 'SameElements', 'SequenceEqual'))
  TUPLE_EQUALITY_ASSERTIONS = frozenset((
      'Equal', 'Equals', 'SameElements', 'SequenceEqual', 'TupleEqual'))
  DICT_EQUALITY_ASSERTIONS = frozenset((
      'CountEqual', 'DictEqual', 'Equal', 'Equals', 'ItemsEqual',
      'SameElements'))
  SET_EQUALITY_ASSERTIONS = frozenset((
      'CountEqual', 'Equal', 'Equals', 'ItemsEqual', 'SameElements',
      'SetEqual'))
  RAISES_REGEX_ASSERTIONS = frozenset((
      'RaisesRegexp', 'RaisesWithRegexpMatch'))

  ANY_QUOTE = '["\']'
  QUOTE_RE = re.compile(ANY_QUOTE)
  CALL_RE = re.compile(r'^[\w.]+\(.*\)', re.S)
  CALL_COUNT_RE = re.compile(r'^([\w.]+)\.call_count$')
  ACTUAL_RE = re.compile(r'actual(?:_|$)')
  EXPECTED_RE = re.compile(r'expected(?:_|$)')
  RESULT_RE = re.compile(r'(?:^|_)result')
  OS_ENVIRON_RE = re.compile(r'^os\.environ')
  LEN_CALL_RE = re.compile(r'^len\(([^)]+)\)$')
  LIST_RE = re.compile(r'^\[.+\]$', re.S)
  TUPLE_RE = re.compile(r'^\(.+\)$', re.S)
  DICT_RE = re.compile(r'^\{.+:.+\}$', re.S)
  SET_RE = re.compile(r'^\{[^:]+\}$', re.S)
  NUMERIC_RE = re.compile(r'^-?\d*(?:\.\d*|E-?\d+|L)?$', re.I)
  STRING_RE = re.compile(r'(?:^[\'"]|[\'"]$)')
  COMPREHENSION_RE = re.compile(r'\sfor\s\S+\sin\s')
  STARTSWITH_RE = re.compile(
      r'^(.+)\.startswith\(([ru]?({0}).*\3)\)$'.format(ANY_QUOTE))
  ENDSWITH_RE = re.compile(
      r'^(.+)\.endswith\(([ru]?({0}).*\3)\)$'.format(ANY_QUOTE))

  def __init__(self, paths):
    self._paths = paths

  def Convert(self):
    """Executes the conversion process."""
    if not self._paths:
      app.usage(shorthelp=True)
      return False

    if not self._Check():
      return False

    success = True
    for path in self._paths:
      success &= self._ConvertFile(path)

    return success

  @classmethod
  def _ConvertFile(cls, path):
    """Converts a single file from unittest to PyTruth.

    Args:
      path: string, the path of file to be converted.

    Returns:
      Boolean: True if the file was successfully converted, otherwise False.
    """
    with open(path) as f:
      src = f.read()

    short_path = os.path.basename(path)
    assertions = 0
    for assertion_re in cls.ASSERTION_RE, cls.MOCK_METHOD_CALL_RE:
      start = 0
      match = assertion_re.search(src, start)
      while match:
        assertion_start = match.start('assertion')
        i = assertion_start + len(match.group('assertion'))
        last_comma = i - 1
        args = []

        depth_round = 1
        depth_curly = 0
        depth_square = 0
        while depth_round:
          if i == len(src):
            line = src[:assertion_start].count('\n') + 1
            snippet = src[assertion_start:src.find('\n', assertion_start)]
            logging.error('Unbalanced parentheses at %s:%d: %s',
                          short_path, line, snippet)
            return False
          elif cls.QUOTE_RE.match(src[i]):
            start_quote = src[i]
            i += 1
            while src[i] != start_quote or src[i-1] == '\\':
              i += 1
          elif src[i] == '#':
            while src[i] != '\n':
              i += 1
          elif src[i] == '(':
            depth_round += 1
          elif src[i] == ')':
            depth_round -= 1
          elif src[i] == '{':
            depth_curly += 1
          elif src[i] == '}':
            depth_curly -= 1
          elif src[i] == '[':
            depth_square += 1
          elif src[i] == ']':
            depth_square -= 1

          if (not depth_curly and not depth_square
              and (src[i] == ',' and depth_round == 1
                   or src[i] == ')' and not depth_round)):
            arg = src[last_comma+1:i].strip()
            if arg:
              args.append(arg)
            last_comma = i

          i += 1

        end = i

        indentation, akey = match.group('indent', 'akey')
        if (akey not in cls.MOCK_METHOD_ASSERTIONS
            and not akey.startswith('Raises')):
          args = args[:2]
        if 'method' in match.groupdict():
          args.insert(0, match.group('method'))

        replacement = cls._GetReplacement(indentation, akey, args)
        logging.debug((start, end, replacement))
        src = ''.join((src[:assertion_start], replacement, src[end:]))
        assertions += 1

        start = assertion_start + len(replacement)
        match = assertion_re.search(src, start)

    output_path = FLAGS.output and os.path.expanduser(FLAGS.output) or path
    with open(output_path, 'w') as f:
      f.write(src)

    logging.info(
        'Converted %s (%d assertion%s)',
        short_path, assertions, '' if assertions == 1 else 's')

    return True

  @classmethod
  def _GetReplacement(cls, indentation, akey, args):
    """Converts a single unittest assertion to PyTruth.

    Args:
      indentation: whitespace characters leading to the unittest assertion.
      akey: a key of UNITTEST_ASSERTIONS or MOCK_METHOD_ASSERTIONS.
      args: iterable of strings, the arguments passed to the unittest method.

    Returns:
      String beginning with "AssertThat("
    """
    more_indentation = FLAGS.indentation.replace('\\t', '\t')
    reversible = (
        len(args) == 2
        and akey in cls.REVERSIBLE_ASSERTIONS
        and (cls.CALL_RE.search(args[1])
             and args[1] not in cls.EMPTY_CONTAINERS
             and not cls.CALL_RE.search(args[0])
             or cls.CALL_COUNT_RE.search(args[1])
             and not cls.CALL_COUNT_RE.search(args[0])
             or cls.NUMERIC_RE.search(args[0])
             and not cls.NUMERIC_RE.search(args[1])
             or cls.STRING_RE.search(args[0])
             and not cls.STRING_RE.search(args[1])
             or cls.ACTUAL_RE.search(args[1])
             and not cls.ACTUAL_RE.search(args[0])
             or cls.EXPECTED_RE.search(args[0])
             and not cls.EXPECTED_RE.search(args[1])
             or cls.RESULT_RE.search(args[1])
             and not cls.RESULT_RE.search(args[0])
             or cls.LIST_RE.search(args[0])
             and not cls.LIST_RE.search(args[1])
             or cls.TUPLE_RE.search(args[0])
             and not cls.TUPLE_RE.search(args[1])
             or cls.DICT_RE.search(args[0])
             and not cls.DICT_RE.search(args[1])
             or cls.SET_RE.search(args[0])
             and not cls.SET_RE.search(args[1])
             or cls.OS_ENVIRON_RE.search(args[1])
             and not cls.OS_ENVIRON_RE.search(args[0])
             or args[0] in cls.EMPTY_CONTAINERS
             and args[1] not in cls.EMPTY_CONTAINERS
             or cls.LEN_CALL_RE.search(args[1])
             and not cls.LEN_CALL_RE.search(args[0])
             or cls.COMPREHENSION_RE.search(args[0])
             and not cls.COMPREHENSION_RE.search(args[0])
             and not cls.CALL_RE.search(args[0])))

    if reversible:
      args.reverse()

    if akey in cls.INEQUALITY_REVERSALS and reversible:
      assertion = cls.INEQUALITY_REVERSALS[akey].format(*args)
    elif akey in cls.UNITTEST_ASSERTIONS:
      assertion = cls.UNITTEST_ASSERTIONS[akey].format(*args)

    if akey in cls.MOCK_METHOD_ASSERTIONS:
      assertion = cls.MOCK_METHOD_ASSERTIONS[akey]
      mock_method = args[0]
      if len(args) == 1:
        assertion = assertion.format(mock_method)
      elif akey == 'has_calls':
        match_any_order = cls.ANY_ORDER_RE.search(args[-1])
        in_order = '.InOrder()'
        if match_any_order:
          args = args[:-1]
          any_order = match_any_order.group(1) not in ('False', 'None', '0')
          if any_order:
            in_order = ''
        assertion = assertion.format(mock_method, args[1], in_order)
      else:
        assertion = assertion.format(mock_method, ', '.join(args[1:]))

    elif len(args) == 1:
      if akey in ('True', '_'):
        match_startswith = cls.STARTSWITH_RE.search(args[0])
        match_endswith = cls.ENDSWITH_RE.search(args[0])
        if match_startswith:
          assertion = '({0}).StartsWith({1})'.format(
              *match_startswith.group(1, 2))
        elif match_endswith:
          assertion = '({0}).EndsWith({1})'.format(
              *match_endswith.group(1, 2))

    elif akey == 'Raises' and len(args) >= 2:
      return ('{0}with AssertThat({2}).IsRaised():\n'
              '{0}{1}{3}({4})').format(
                  indentation, more_indentation,
                  args[0], args[1], ', '.join(args[2:]))

    elif akey in cls.RAISES_REGEX_ASSERTIONS and len(args) >= 3:
      return ('{0}with AssertThat({2}).IsRaised(matching={3}):\n'
              '{0}{1}{4}({5})').format(
                  indentation, more_indentation,
                  args[0], args[1], args[2], ', '.join(args[3:]))

    elif len(args) == 2:
      if 'NotEqual' in akey:
        if args[1] == 'True':
          assertion = '({0}).IsFalse()'.format(args[0])
        elif args[1] == 'False':
          assertion = '({0}).IsTrue()'.format(args[0])
        elif args[1] == 'None':
          assertion = '({0}).IsNotNone()'.format(args[0])
        elif args[1] in cls.EMPTY_CONTAINERS:
          assertion = '({0}).IsNotEmpty()'.format(args[0])
        elif args[1] == '0':
          match_len = cls.LEN_CALL_RE.search(args[0])
          if match_len:
            assertion = '({0}).IsNotEmpty()'.format(match_len.group(1))
          else:
            assertion = '({0}).IsNonZero()'.format(args[0])

      elif 'Equal' in akey or akey in cls.MEMBERSHIP_ASSERTIONS:
        if args[1] == 'True':
          assertion = '({0}).IsTrue()'.format(args[0])
        elif args[1] == 'False':
          assertion = '({0}).IsFalse()'.format(args[0])
        elif args[1] == 'None':
          assertion = '({0}).IsNone()'.format(args[0])
        elif args[1] in cls.EMPTY_CONTAINERS:
          assertion = '({0}).IsEmpty()'.format(args[0])
        elif (cls.LIST_RE.search(args[1])
              and akey in cls.LIST_EQUALITY_ASSERTIONS
              or cls.TUPLE_RE.search(args[1])
              and akey in cls.TUPLE_EQUALITY_ASSERTIONS):
          els_in = 'ElementsIn' if cls.COMPREHENSION_RE.search(args[1]) else ''
          order = ''
          if (akey not in cls.MEMBERSHIP_ASSERTIONS
              and (els_in or ',' in args[1])):
            order = '.InOrder()'
          assertion = '({0}).ContainsExactly{1}({2}){3}'.format(
              args[0], els_in, args[1][1:-1].strip(), order)
        elif (cls.DICT_RE.search(args[1])
              and akey in cls.DICT_EQUALITY_ASSERTIONS):
          assertion = '({0}).ContainsExactlyItemsIn({1})'.format(
              args[0], args[1])
        elif (cls.SET_RE.search(args[1])
              and akey in cls.SET_EQUALITY_ASSERTIONS):
          els_in = 'ElementsIn' if cls.COMPREHENSION_RE.search(args[1]) else ''
          assertion = '({0}).ContainsExactly{1}({2})'.format(
              args[0], els_in, args[1][1:-1].strip())
        elif args[1] == '0':
          match_len = cls.LEN_CALL_RE.search(args[0])
          if match_len:
            assertion = '({0}).IsEmpty()'.format(match_len.group(1))
          else:
            match_call_count = cls.CALL_COUNT_RE.search(args[0])
            if match_call_count:
              mock_method = match_call_count.group(1)
              assertion = '({0}).WasNotCalled()'.format(mock_method)
            else:
              assertion = '({0}).IsZero()'.format(args[0])
        else:
          match_len = cls.LEN_CALL_RE.search(args[0])
          if match_len:
            assertion = '({0}).HasSize({1})'.format(match_len.group(1), args[1])
          else:
            match_call_count = cls.CALL_COUNT_RE.search(args[0])
            if match_call_count:
              mock_method = match_call_count.group(1)
              if args[1] == '1':
                assertion = '({0}).WasCalled().Once()'.format(mock_method)
              else:
                assertion = '({0}).WasCalled().Times({1})'.format(
                    mock_method, args[1])

      elif akey == 'In':
        if cls.LIST_RE.search(args[1]) or cls.TUPLE_RE.search(args[1]):
          assertion = '({0}).IsAnyOf({1})'.format(
              args[0], args[1][1:-1].strip())

      elif akey == 'NotIn':
        if cls.LIST_RE.search(args[1]) or cls.TUPLE_RE.search(args[1]):
          assertion = '({0}).IsNoneOf({1})'.format(
              args[0], args[1][1:-1].strip())

      elif akey == 'Len':
        if args[1] == '0':
          assertion = '({0}).IsEmpty()'.format(args[0])
        else:
          assertion = '({0}).HasSize({1})'.format(args[0], args[1])

    return '{0}AssertThat{1}'.format(indentation, assertion)

  def _Check(self):
    """Verifies the existence and read+write access to all paths.

    Returns:
      Boolean, True if all paths are OK, otherwise False.
    """
    success = True
    for path in self._paths:
      if not os.path.isfile(path):
        logging.error('No such file: %s', path)
        success = False
      elif not os.access(path, os.R_OK):
        logging.error('No read access: %s', path)
        success = False
      elif not FLAGS.output and not os.access(path, os.W_OK):
        logging.error('No write access: %s', path)
        success = False

    return success


def main(args):
  return 0 if Converter(args[1:]).Convert() else 1


def DefineFlags():
  flags.DEFINE_string(
      'indentation', '  ',
      'Indentation characters when creating "with" contexts.'
      ' "\\t" is recognized as a tab character.')
  flags.DEFINE_string(
      'output', None,
      'Output file path. By default, files are converted in-place.')


if __name__ == '__main__':
  DefineFlags()
  app.run(main)
