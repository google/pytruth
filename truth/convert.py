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
  - The import of the truth module is not added.
  - The assignment "AssertThat = truth.AssertThat" is not added.
  - Conversions may cause lines to increase in length.
  - Conversions may modify indentation and line wrapping.
  - Converts all instance of assertTrue(a) to AssertThat(a).IsTrue().
    In unittest, assertTrue() asserts *truthiness*, while PyTruth's IsTrue()
    matches only True itself. You may need to modify some IsTrue() assertions
    to IsTruthy(), and likewise for assertFalse(), IsFalse(), and IsFalsy().
  - Converts assertEqual(len(str), n) to AssertThat(str).HasSize(n).
    This works, but HasLength(n) is actually more appropriate.
  - Does not convert mock function assertions.
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

  ASSERTION_RE = re.compile(r'(([ \t]*)self\.assert({0})\s*\()'.format(
      r'|'.join(UNITTEST_ASSERTIONS)))

  EMPTY_CONTAINERS = frozenset((
      "''", '""', "r''", 'r""', "u''", 'u""',
      '()', '[]', '{}', 'dict()', 'list()', 'set()', 'tuple()',
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
    start = 0
    match = cls.ASSERTION_RE.search(src, start)
    while match:
      i = match.start(1) + len(match.group(1))
      last_comma = i - 1
      args = []

      depth_round = 1
      depth_curly = 0
      depth_square = 0
      while depth_round:
        if i == len(src):
          line = src[:match.start(1)].count('\n') + 1
          snippet = src[match.start(1):src.find('\n', match.start(1))]
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
          args.append(src[last_comma+1:i].strip())
          last_comma = i

        i += 1

      end = i
      indentation, ut_key = match.group(2, 3)
      if not ut_key.startswith('Raises'):
        args = args[:2]

      replacement = cls._GetReplacement(indentation, ut_key, args)
      logging.debug((start, end, replacement))
      src = ''.join((src[:match.start(1)], replacement, src[end:]))
      assertions += 1

      start = match.start(1) + len(replacement)
      match = cls.ASSERTION_RE.search(src, start)

    output_path = FLAGS.output and os.path.expanduser(FLAGS.output) or path
    with open(output_path, 'w') as f:
      f.write(src)

    logging.info(
        'Converted %s (%d assertion%s)',
        short_path, assertions, '' if assertions == 1 else 's')

    return True

  @classmethod
  def _GetReplacement(cls, indentation, ut_key, args):
    """Converts a single unittest assertion to PyTruth.

    Args:
      indentation: whitespace characters leading to the unittest assertion.
      ut_key: unittest key, a key of UNITTEST_ASSERTIONS.
      args: iterable of strings, the arguments passed to the unittest method.

    Returns:
      String beginning with "AssertThat("
    """
    more_indentation = FLAGS.indentation.replace('\\t', '\t')
    reversible = (
        len(args) == 2
        and ut_key in cls.REVERSIBLE_ASSERTIONS
        and (cls.CALL_RE.search(args[1])
             and args[1] not in cls.EMPTY_CONTAINERS
             and not cls.CALL_RE.search(args[0])
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
             and cls.NUMERIC_RE.search(args[0])
             or cls.COMPREHENSION_RE.search(args[0])
             and not cls.COMPREHENSION_RE.search(args[0])
             and not cls.CALL_RE.search(args[0])))

    if reversible:
      args.reverse()

    if ut_key in cls.INEQUALITY_REVERSALS and reversible:
      assertion = cls.INEQUALITY_REVERSALS[ut_key].format(*args)
    else:
      assertion = cls.UNITTEST_ASSERTIONS[ut_key].format(*args)

    if len(args) == 1:
      if ut_key in ('True', '_'):
        match_startswith = cls.STARTSWITH_RE.search(args[0])
        match_endswith = cls.ENDSWITH_RE.search(args[0])
        if match_startswith:
          assertion = '({0}).StartsWith({1})'.format(
              *match_startswith.group(1, 2))
        elif match_endswith:
          assertion = '({0}).EndsWith({1})'.format(
              *match_endswith.group(1, 2))

    elif ut_key == 'Raises' and len(args) >= 2:
      return ('{0}with AssertThat({2}).IsRaised():\n'
              '{0}{1}{3}({4})').format(
                  indentation, more_indentation,
                  args[0], args[1], ', '.join(args[2:]))

    elif ut_key in cls.RAISES_REGEX_ASSERTIONS and len(args) >= 3:
      return ('{0}with AssertThat({2}).IsRaised(matching={3}):\n'
              '{0}{1}{4}({5})').format(
                  indentation, more_indentation,
                  args[0], args[1], args[2], ', '.join(args[3:]))

    elif len(args) == 2:
      if 'NotEqual' in ut_key:
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

      elif 'Equal' in ut_key or ut_key in cls.MEMBERSHIP_ASSERTIONS:
        if args[1] == 'True':
          assertion = '({0}).IsTrue()'.format(args[0])
        elif args[1] == 'False':
          assertion = '({0}).IsFalse()'.format(args[0])
        elif args[1] == 'None':
          assertion = '({0}).IsNone()'.format(args[0])
        elif args[1] in cls.EMPTY_CONTAINERS:
          assertion = '({0}).IsEmpty()'.format(args[0])
        elif (cls.LIST_RE.search(args[1])
              and ut_key in cls.LIST_EQUALITY_ASSERTIONS
              or cls.TUPLE_RE.search(args[1])
              and ut_key in cls.TUPLE_EQUALITY_ASSERTIONS):
          els_in = 'ElementsIn' if cls.COMPREHENSION_RE.search(args[1]) else ''
          order = ''
          if (ut_key not in cls.MEMBERSHIP_ASSERTIONS
              and (els_in or ',' in args[1])):
            order = '.InOrder()'
          assertion = '({0}).ContainsExactly{1}({2}){3}'.format(
              args[0], els_in, args[1][1:-1].strip(), order)
        elif (cls.DICT_RE.search(args[1])
              and ut_key in cls.DICT_EQUALITY_ASSERTIONS):
          assertion = '({0}).ContainsExactlyItemsIn({1})'.format(
              args[0], args[1])
        elif (cls.SET_RE.search(args[1])
              and ut_key in cls.SET_EQUALITY_ASSERTIONS):
          els_in = 'ElementsIn' if cls.COMPREHENSION_RE.search(args[1]) else ''
          assertion = '({0}).ContainsExactly{1}({2})'.format(
              args[0], els_in, args[1][1:-1].strip())
        elif args[1] == '0':
          match_len = cls.LEN_CALL_RE.search(args[0])
          if match_len:
            assertion = '({0}).IsEmpty()'.format(match_len.group(1))
          else:
            assertion = '({0}).IsZero()'.format(args[0])
        else:
          match_len = cls.LEN_CALL_RE.search(args[0])
          if match_len and cls.NUMERIC_RE.search(args[1]):
            assertion = '({0}).HasSize({1})'.format(match_len.group(1), args[1])

      elif ut_key == 'In':
        if cls.LIST_RE.search(args[1]) or cls.TUPLE_RE.search(args[1]):
          assertion = '({0}).IsAnyOf({1})'.format(
              args[0], args[1][1:-1].strip())

      elif ut_key == 'NotIn':
        if cls.LIST_RE.search(args[1]) or cls.TUPLE_RE.search(args[1]):
          assertion = '({0}).IsNoneOf({1})'.format(
              args[0], args[1][1:-1].strip())

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
