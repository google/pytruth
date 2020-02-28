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

"""Truth - a proposition framework for tests.

Provides Truth-style assertion and assumption semantics in a fluent style.
Translated from the Java source, https://github.com/google/truth.

Import the AssertThat() method to gain access to the module's capabilities:
  from truth.truth import AssertThat

Alternatively:
  from truth import truth
  AssertThat = truth.AssertThat      # pylint: disable=invalid-name

Then, instead of writing:
  self.assertEqual(a, b)
  self.assertTrue(c)
  self.assertIn(a, d)
  self.assertTrue(a in d and b in d)
  self.assertTrue(a in d or b in d or c in d)
  with self.assertRaises(Error):
    Explode()

one would write:
  AssertThat(a).IsEqualTo(b)
  AssertThat(c).IsTrue()
  AssertThat(d).Contains(a)
  AssertThat(d).ContainsAllOf(a, b)
  AssertThat(d).ContainsAnyOf(a, b, c)
  with AssertThat(Error).IsRaised():
    Explode()

Tests should be easier to read and write, and flow more clearly.

Often, tests assert a relationship between a value produced by the test
(the "actual" value) and some reference value (the "expected" value). It is
strongly recommended that the actual value is made the subject of the assertion.
For example:

  AssertThat(actual).IsEqualTo(expected)     # Recommended.
  AssertThat(expected).IsEqualTo(actual)     # Not recommended.
  AssertThat(actual).IsIn(expected_possibilities)      # Recommended.
  AssertThat(expected_possibilities).Contains(actual)  # Not recommended.

For users of the Java Truth library, all method names have been preserved,
except that their first letters are capitalized for Python naming style.
Also, dictionaries' methods containing the Java terms "Entry" or "Entries" are
aliased to ones with the Python terms "Item" or "Items", which are preferred.

In addition, some subjects have been augmented with free inherited propositions.
For instance, Java Strings are not directly iterable, but Python strings are,
so any iterable-related propositions just work:
  AssertThat('abcdefg').ContainsAllOf('a', 'c', 'e').InOrder()
  AssertThat('abcdefg').IsStrictlyOrdered()

Subject class hierarchy:
  _EmptySubject
    |-- _DefaultSubject
    |     |-- _BooleanSubject
    |     |-- _ClassSubject
    |     |     `-- _ExceptionClassSubject
    |     |-- _ExceptionSubject
    |     |-- _ComparableSubject
    |     |     `-- _NumericSubject
    |     |-- _IterableSubject
    |     `-- _NamedMockSubject
    |           |-- _MockSubject
    |           |-- _MockCalledSubject
    |           `-- _MockCalledWithSubject
    |
    |-- _Ordered
    |     |-- _InOrder
    |     `-- _NotInOrder
    |
    |-- _TolerantNumericSubject

Multiply-inherited classes:
    `-- _DefaultSubject
          |-- (_ComparableSubject + _IterableSubject)
          |      `-- _ComparableIterableSubject
          |            |-- _DictionarySubject
          |            `-- _StringSubject
          |
          `-- (_BooleanSubject + _ClassSubject + _DictionarySubject + ...
               _ExceptionSubject + _MockSubject + _NumericSubject + ...
               _StringSubject)
                 `-- _NoneSubject

Some subjects may yield secondary subjects once successfully asserted:
  * _IterableSubject -> _Ordered
  * _NumericSubject -> _TolerantNumericSubject
  * _MockSubject -> _MockCalledSubject

It is an error to leave an assertion subject unresolved:
  AssertThat(thing)
  AssertThat(number).IsWithin(0.1)
both raise UnresolvedAssertionError upon the interpreter exiting.

This module is threadsafe in that you may execute multiple assertions in
parallel so long as they are all resolved by the time the interpreter exits.
Note that if the iterator over a shared value (either expected or actual)
changes the value or its underlying elements, the behavior is undefined:
all, none, or some of the assertions may succeed or fail, arbitrarily.
If you discover a concurrency bug, please report it or fix it.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import atexit
import collections
import difflib
import imp
import inspect
import math
import numbers
import os
import re
import threading

try:
  from unittest import mock
except ImportError:
  from mock import mock

import six
from six.moves import zip

try:
  import collections.abc as collections_abc
except ImportError:
  import collections as collections_abc  # pylint: disable=reimported


# All these attributes must be present for an object to be deemed comparable.
_COMPARABLE_ATTRS = frozenset(
    '__{0}__'.format(attr) for attr in ('lt', 'le', 'gt', 'ge'))


# All these attributes must be present for an object to be recognized as a mock.
_MOCK_ATTRS = frozenset((
    'called', 'assert_called_with', 'reset_mock', 'return_value'))


# Special numeric concepts.
POSITIVE_INFINITY = float('inf')
NEGATIVE_INFINITY = float('-inf')
NAN = float('nan')

# pylint: disable=invalid-name,undefined-variable
Cmp = cmp if six.PY2 else lambda a, b: (a > b) - (a < b)
# pylint: enable=invalid-name,undefined-variable


# Make a copy of all members of <os> and <os.path>, and inject them into the
# inspect module's import of <os>. This prevents mocked versions of their
# functions from being called when subjects are instantiated, allowing multiple
# assertions to execute in parallel safely. We can't simply stub inspect.os or
# inspect.os.path alone, because they are references to module singletons.
inspect.os = imp.new_module('os_for_inspect')
for os_key in dir(os):
  setattr(inspect.os, os_key, getattr(os, os_key))
inspect.os.path = imp.new_module('os_path_for_inspect')
for path_key in dir(os.path):
  setattr(inspect.os.path, path_key, getattr(os.path, path_key))


class TruthAssertionError(AssertionError):
  """Exception raised by all failed assertions in this module."""


class InvalidAssertionError(TruthAssertionError):
  """An invalid assertion was attempted."""


class UnresolvedAssertionError(TruthAssertionError):
  """A return value from an AssertThat() was not used."""


class UnresolvedExceptionError(UnresolvedAssertionError):
  """A return value from an AssertThat(Exception) was not used."""


def AssertThat(target):
  """Gateway function that initiates an assertion.

  Args:
    target: any object whatsoever, the object under test.

  Returns:
    A subject appropriate for the target.
  """

  # All types descend from "type", so check if target is a type itself first.
  # pylint: disable=unidiomatic-typecheck
  if type(target) is type:
    if issubclass(target, BaseException):
      return _ExceptionClassSubject(target)
    return _ClassSubject(target)
  # pylint: enable=unidiomatic-typecheck

  for super_type, subject_class in six.iteritems(_TYPE_CONSTRUCTORS):
    # Must use issubclass() and not isinstance(), because mocked functions
    # override their __class__. See mock._is_instance().
    if issubclass(type(target), super_type):
      return subject_class(target)

  if _IsMock(target):
    return _MockSubject(target)
  if _IsNumeric(target):
    return _NumericSubject(target)
  if _IsComparable(target) and _IsIterable(target):
    return _ComparableIterableSubject(target)
  if _IsComparable(target):
    return _ComparableSubject(target)
  if _IsIterable(target):
    return _IterableSubject(target)

  return _DefaultSubject(target)


def _IsComparable(target):
  """Returns True if the target is comparable.

  Many things are considered comparable. An important exception is None, which
  in Python 2 compares less than anything besides None. None is a special case
  handled by _NoneSubject, so it's irrelevant what this returns for None.

  Args:
    target: any object whatsoever.

  Returns:
    True if the target is comparable, otherwise False.
  """
  if _IsNumeric(target):
    return True
  for attr in _COMPARABLE_ATTRS:
    if not hasattr(target, attr):
      return False
  return True


def _IsHashable(target):
  """Returns True if the target is hashable."""
  if not hasattr(target, '__hash__') or not target.__hash__:
    return False
  try:
    hash(target)
  except (TypeError, ValueError):
    return False
  return True


def _IsIterable(target):
  """Returns True if the target is iterable."""
  try:
    return isinstance(target, collections_abc.Iterable)
  except (AttributeError, TypeError):
    return False


def _IsMock(target):
  """Returns True if the target is a mock."""
  if isinstance(target, mock.NonCallableMock):
    return True
  for attr in _MOCK_ATTRS:
    if not hasattr(target, attr):
      return False
  return True


def _IsNumeric(target):
  """Returns True if the target is a number."""
  try:
    return isinstance(target, numbers.Number)
  except (AttributeError, TypeError):
    return False


def _DescribeTimes(times):
  return 'once' if times == 1 else '{0} times'.format(times)


def asserts_truth(func):  # pylint: disable=invalid-name
  """Decorator for every public method that might raise TruthAssertionError.

  Args:
    func: the function to be decorated.

  Returns:
    The decorated function. In Python 2, the function behaves identically.
    Otherwise, if that function raises a TruthAssertionError, then that error
    is re-raised with a modified, minimal traceback.

  Raises:
    AttributeError: if attempted to be applied to a method whose name begins
        with a single '_'. This decorator's purpose is to reduce the traceback
        depth of exceptions raised by nested calls in this library, so that the
        failing assertion has only two frames: the original AssertThat() call,
        and the "raise truth_assertion" in the decorated function.
        Annotating inner method calls is contrary to that goal.
  """
  if re.match(r'_[^_]', func.__name__):
    raise AttributeError(
        '@asserts_truth may not be applied to methods beginning with "_".')

  def AssertThat(*args, **kwargs):  # pylint: disable=redefined-outer-name
    try:
      return func(*args, **kwargs)
    except TruthAssertionError as truth_assertion:
      if hasattr(truth_assertion, 'with_traceback'):
        truth_assertion.with_traceback(None)
        raise truth_assertion
      raise

  return AssertThat


class _EmptySubject(object):
  """Base class for all subjects.

  The empty subject cannot test anything; it provides only methods for failing.
  """

  _unresolved_subjects = set()
  _unresolved_subjects_lock = threading.RLock()

  def __init__(self, actual):
    self.__actual = actual
    self._name = None
    self._stack = inspect.stack()
    with self._unresolved_subjects_lock:
      self._unresolved_subjects.add(self)

  def __str__(self):
    stack_iter = iter(self._stack)
    for stack in stack_iter:
      # Find the caller of AssertThat(...).
      if stack[3] == 'AssertThat':
        caller = next(stack_iter)
        return ('{0}({1}) created in module {2}, line {3}, in {4}:\n'
                '      {5}'
                .format(self.__class__.__name__, self._GetSubject(),
                        inspect.getmodulename(caller[1]),   # Module name.
                        caller[2],                          # Line number.
                        caller[3],                          # Function name.
                        caller[4][0].strip()))              # Code snippet.

    # The subject was not created by AssertThat().
    return '{0}({1})'.format(self.__class__.__name__, self._GetSubject())

  def Named(self, name):
    """Adds a prefix to the subject, when it is displayed in error messages.

    This is especially useful in the context of types that have no helpful
    string representation (e.g., boolean). Writing
      AssertThat(foo).Named('foo').IsTrue()
    then results in a more reasonable error.

    Args:
      name: string, the name to display along with the actual value.

    Returns:
      self
    """
    self._name = name
    return self

  @property
  def name(self):
    return self._name

  @property
  def _actual(self):
    self._Resolve()
    return self.__actual

  @_actual.setter
  def _actual(self, value):
    self.__actual = value

  @classmethod
  def _CheckUnresolved(cls):
    """Ensures that all created subjects were eventually resolved.

    A subject is considered resolved what at least one proposition has been
    executed on it. An unresolved or dangling assertion is almost certainly a
    test author error.

    Raises:
      UnresolvedAssertionError: if any subjects remain unresolved at the time of
          this function call.
    """
    with cls._unresolved_subjects_lock:
      if cls._unresolved_subjects:
        msg = ['The following assertions were unresolved. Perhaps you called'
               ' "AssertThat(thing.IsEmpty())" instead of'
               ' "AssertThat(thing).IsEmpty()".']
        for u in sorted(cls._unresolved_subjects):
          msg.append('    * {0}'.format(u))
        raise UnresolvedAssertionError('\n'.join(msg))

  def _Resolve(self):
    """Marks the current subject as having been adequately asserted."""
    with self._unresolved_subjects_lock:
      if self in self._unresolved_subjects:
        self._unresolved_subjects.remove(self)

  @classmethod
  def _ResolveAll(cls):
    """Marks all subject as having been adequately asserted.

    This should be called only by tests that create unresolved subjects.
    """
    with cls._unresolved_subjects_lock:
      cls._unresolved_subjects.clear()

  def _GetSubject(self):
    if self._name:
      return '{0}(<{1!r}>)'.format(self._name, self.__actual)
    return '<{0!r}>'.format(self.__actual)

  def _FailComparingValues(self, verb, other, suffix=''):
    self._FailWithProposition('{0} <{1!r}>'.format(verb, other), suffix=suffix)

  def _FailWithBadResults(self, verb, other, fail_verb, actual, suffix=''):
    self._FailWithProposition(
        '{0} <{1!r}>. It {2} <{3}>'
        .format(verb, other, fail_verb, actual), suffix=suffix)

  def _FailWithProposition(self, proposition, suffix=''):
    self._Fail(
        'Not true that {0} {1}.{2}'
        .format(self._GetSubject(), proposition, suffix))

  def _FailWithSubject(self, verb):
    self._Fail('{0} {1}.'.format(self._GetSubject(), verb))

  def _Fail(self, msg):
    """Fail unconditionally.

    Args:
      msg: string to include in the exception.

    Raises:
      TruthAssertionError: always, by design.
    """
    raise TruthAssertionError(msg)


class _DefaultSubject(_EmptySubject):
  """Subject for anything not more specific.

  All other subjects should subclass this.
  """

  @asserts_truth
  def IsEqualTo(self, other):
    if self._actual != other:
      suffix = ''
      if str(self._actual) == str(other):
        suffix = ' However, their str() representations are equal.'
      elif repr(self._actual) == repr(other):
        suffix = ' However, their repr() representations are equal.'
      self._FailComparingValues('is equal to', other, suffix=suffix)

  @asserts_truth
  def IsNotEqualTo(self, other):
    if self._actual == other:
      self._FailComparingValues('is not equal to', other)

  @asserts_truth
  def IsNone(self):
    if self._actual is not None:
      self._FailWithProposition('is None')

  @asserts_truth
  def IsNotNone(self):
    if self._actual is None:
      self._FailWithProposition('is not None')

  @asserts_truth
  def IsIn(self, iterable):
    if self._actual not in iterable:
      self._FailComparingValues('is equal to any of', iterable)

  @asserts_truth
  def IsNotIn(self, iterable):
    """Asserts that this subject is not a member of the given iterable."""
    if hasattr(iterable, 'index'):
      try:
        index = iterable.index(self._actual)
        self._FailWithProposition(
            'is not in {0!r}. It was found at index {1}'
            .format(iterable, index))
      except ValueError:
        pass
    else:
      if self._actual in iterable:
        self._FailWithProposition('is not in {0!r}'.format(iterable))

  @asserts_truth
  def IsAnyOf(self, *iterable):
    return self.IsIn(iterable)

  @asserts_truth
  def IsNoneOf(self, *iterable):
    return self.IsNotIn(iterable)

  @asserts_truth
  def IsInstanceOf(self, cls):
    if not isinstance(self._actual, cls):
      self._FailWithBadResults(
          'is an instance of', cls, 'is an instance of', type(self._actual))

  @asserts_truth
  def IsNotInstanceOf(self, cls):
    if isinstance(self._actual, cls):
      self._FailWithSubject(
          'expected not to be an instance of {0}, but was'.format(cls))

  @asserts_truth
  def IsSameAs(self, other):
    if self._actual is not other:
      self._FailComparingValues('is the same instance as', other)

  @asserts_truth
  def IsNotSameAs(self, other):
    if self._actual is other:
      self._FailComparingValues('is not the same instance as', other)

  @asserts_truth
  def IsTruthy(self):
    if not self._actual:
      self._FailWithProposition('is truthy')

  @asserts_truth
  def IsFalsy(self):
    if self._actual:
      self._FailWithProposition('is falsy')

  @asserts_truth
  def IsTrue(self):
    suffix = ''
    if self._actual:
      suffix = (' However, it is truthy.'
                ' Did you mean to call IsTruthy() instead?')
    self._FailWithProposition('is True', suffix=suffix)

  @asserts_truth
  def IsFalse(self):
    suffix = ''
    if not self._actual:
      suffix = ' However, it is falsy. Did you mean to call IsFalsy() instead?'
    self._FailWithProposition('is False', suffix=suffix)

  # Recognize alternate spelling.
  # pylint: disable=invalid-name
  IsFalsey = IsFalsy
  # pylint: enable=invalid-name

  @asserts_truth
  def HasAttribute(self, attr):
    if not hasattr(self._actual, attr):
      self._FailComparingValues('has attribute', attr)

  @asserts_truth
  def DoesNotHaveAttribute(self, attr):
    if hasattr(self._actual, attr):
      self._FailComparingValues('does not have attribute', attr)

  @asserts_truth
  def IsCallable(self):
    if not callable(self._actual):
      self._FailWithProposition('is callable')

  @asserts_truth
  def IsNotCallable(self):
    if callable(self._actual):
      self._FailWithProposition('is not callable')


class _UnresolvedContextMixin(object):
  """Transform the current subject into a context that fails unconditionally.

  In the case where the developer writes this incorrect context:
    with AssertThat(Error):
      ...

  Python fails with a cryptic stack trace "AttributeError: __exit__". Raise a
  more helpful exception instructing the developer to complete the assertion.
  """

  def __enter__(self):
    raise UnresolvedExceptionError(
        'Exception subject was initiated but not resolved.'
        ' Did you forget to call IsRaised()?')

  def __exit__(self, exc_type, exc, exc_tb):
    """This method must merely exist to be recognized as a context."""


class _ExceptionSubject(_DefaultSubject, _UnresolvedContextMixin):
  """Subject for exceptions (i.e., instances of BaseException)."""

  @asserts_truth
  def HasMessage(self, expected):
    AssertThat(self._GetActualMessage()).IsEqualTo(expected)

  def HasMessageThat(self):
    return AssertThat(self._GetActualMessage())

  def HasArgsThat(self):
    return AssertThat(self._actual.args)

  def IsRaised(self):
    """Asserts that an exception matching this subject is raised.

    The raised exception must be the same type as (or a subclass of) this
    subject's. The raised exception's "message" and "args" attributes must
    match this subject's exactly. As this is a fairly strict match,
    _ExceptionClassSubject.IsRaised() may be easier to use.

    Returns:
      A context within which an expected exception may be raised.
    """

    class IsRaisedContext(_EmptySubject):
      """Context for code under test that is expected to raise an exception."""

      def __init__(self, actual, get_actual_message):
        super(IsRaisedContext, self).__init__(actual)
        self._get_actual_message = get_actual_message

      def __enter__(self):
        return self

      @asserts_truth
      def __exit__(self, exc_type, exc, exc_tb):
        if exc:
          if issubclass(exc_type, type(self._actual)):
            if hasattr(self._actual, 'message'):
              AssertThat(exc).HasMessage(self._get_actual_message())
            AssertThat(exc).HasArgsThat().ContainsExactlyElementsIn(
                self._actual.args).InOrder()
          else:
            self._FailWithSubject(
                'should have been raised, but caught <{0!r}>'.format(exc))
        else:
          self._Resolve()
          self._FailWithSubject('should have been raised, but was not')
        return True

    return IsRaisedContext(self._actual, self._GetActualMessage)

  def _GetActualMessage(self):
    """Returns the "message" portion of an exception.

    Many Python 2 exceptions have a "message" attribute, so return that directly
    in Python 2. However, this attribute is never present in Python 3, so return
    the first argument passed to the exception instance as the message.

    Returns:
      String
    """
    if six.PY2:
      return self._actual.message
    return self._actual.args[0] if self._actual.args else ''


class _BooleanSubject(_DefaultSubject):
  """Subject for booleans."""

  @asserts_truth
  def IsTrue(self):
    if self._actual is not True:
      self._FailWithSubject(
          'was expected to be True, but was {0}'.format(self._actual))

  @asserts_truth
  def IsFalse(self):
    if self._actual is not False:
      self._FailWithSubject(
          'was expected to be False, but was {0}'.format(self._actual))


class _ClassSubject(_DefaultSubject):
  """Subject for classes."""

  @asserts_truth
  def IsSubclassOf(self, other):
    """Fails if this is not the same as, or a subclass of, the given class."""
    if not issubclass(self._actual, other):
      self._FailComparingValues('is a subclass of', other)


class _ExceptionClassSubject(_ClassSubject, _UnresolvedContextMixin):
  """Subject for exception classes (i.e., subclasses of BaseException)."""

  def IsRaised(self, matching=None, containing=None):
    """Asserts that an exception matching this subject is raised.

    The raised exception must be the same type as (or a subclass of) this
    subject's. None, one, or both of matching= and containing= may be specified.

    Args:
      matching: string or regex object. If present, the raised exception's
          "message" attribute must contain this value, as a regular expression.
      containing: string. If present, the raised exception's "message" attribute
          must contain this literal string value.

    Returns:
      A context within which an expected exception may be raised and tested.
    """

    class IsRaisedContext(_EmptySubject):
      """Context for code under test that is expected to raise an exception."""

      def __init__(self, actual, matching=None, containing=None):
        super(IsRaisedContext, self).__init__(actual)
        self._matching = matching
        self._containing = containing

      def __enter__(self):
        return self

      @asserts_truth
      def __exit__(self, exc_type, exc, exc_tb):
        if exc:
          if issubclass(exc_type, self._actual):
            if self._matching is not None:
              AssertThat(exc).HasMessageThat().ContainsMatch(self._matching)
            if self._containing is not None:
              AssertThat(exc).HasMessageThat().Contains(self._containing)
          else:
            self._FailWithSubject(
                'should have been raised, but caught <{0!r}>'.format(exc))
        else:
          self._Resolve()
          self._FailWithSubject('should have been raised, but was not')
        return True

    return IsRaisedContext(
        self._actual, matching=matching, containing=containing)


class _ComparableSubject(_DefaultSubject):
  """Subject for things that are comparable using the < > <= >= operators."""

  @asserts_truth
  def IsAtLeast(self, other):
    self._CheckNone('IsAtLeast', other)
    if self._actual < other:
      self._FailComparingValues('is at least', other)

  @asserts_truth
  def IsAtMost(self, other):
    self._CheckNone('IsAtMost', other)
    if self._actual > other:
      self._FailComparingValues('is at most', other)

  @asserts_truth
  def IsGreaterThan(self, other):
    self._CheckNone('IsGreaterThan', other)
    if self._actual <= other:
      self._FailComparingValues('is greater than', other)

  @asserts_truth
  def IsLessThan(self, other):
    self._CheckNone('IsLessThan', other)
    if self._actual >= other:
      self._FailComparingValues('is less than', other)

  def _CheckNone(self, proposition, other):
    if other is None and not six.PY2:
      raise InvalidAssertionError(
          'It is illegal to compare using {0}({1})'.format(proposition, None))


class _DuplicateCounter(object):
  """A synchronized collection of counters for tracking duplicates.

  The count values may be modified only through Increment() and Decrement(),
  which increment and decrement by 1 (only). If a count ever becomes 0, the item
  is immediately expunged from the dictionary. Counts can never be negative;
  attempting to Decrement an absent key has no effect.

  Implements some dictionary methods: len(d) and "k in d" are supported.

  Order is preserved so that error messages containing expected values match.

  Supports counting unhashable objects, including objects that embed unhashable
  objects. Hashable objects are tracked in O(1) time. Unhashable objects are
  tracked in O(n) time, where n is the number of unhashable objects being
  tracked so far.

  This class is threadsafe.
  """

  def __init__(self):
    self._d = collections.OrderedDict()
    self._unhashable_items = []
    self._unhashable_counts = []
    self._lock = threading.Lock()

  def __contains__(self, key):
    with self._lock:
      if _IsHashable(key):
        return key in self._d
      return key in self._unhashable_items

  def __len__(self):
    with self._lock:
      return len(self._d) + len(self._unhashable_items)

  def __str__(self):
    """Returns the string representation of the duplicate counts.

    Items occurring more than once are accompanied by their count.
    Otherwise the count is implied to be 1.

    For example, if the internal dict is {2: 1, 3: 4, 'abc': 1}, this returns
    the string "[{2, 3 [4 copies], 'abc'}]".

    Returns:
      String, the counts of duplicate items.
    """
    duplicates = []
    def AppendDuplicateItem(item, count):
      if count == 1:
        duplicates.append('{0!r}'.format(item))
      else:
        duplicates.append('{0!r} [{1} copies]'.format(item, count))

    with self._lock:
      for item, count in six.iteritems(self._d):
        AppendDuplicateItem(item, count)
      for item, count in zip(self._unhashable_items, self._unhashable_counts):
        AppendDuplicateItem(item, count)
    return '[{0}]'.format(', '.join(duplicates))

  def Increment(self, key):
    """Atomically increment a count by 1. Insert the item if not present.

    Args:
      key: the key being counted.
    """
    with self._lock:
      if _IsHashable(key):
        if key in self._d:
          self._d[key] += 1
        else:
          self._d[key] = 1
      else:
        try:
          i = self._unhashable_items.index(key)
          self._unhashable_counts[i] += 1
        except ValueError:
          self._unhashable_items.append(key)
          self._unhashable_counts.append(1)

  def Decrement(self, key):
    """Atomically decrement a count by 1. Expunge the item if the count is 0.

    If the item is not present, has no effect.

    Args:
      key: the key being counted.
    """
    with self._lock:
      if _IsHashable(key):
        if key in self._d:
          if self._d[key] > 1:
            self._d[key] -= 1
          else:
            del self._d[key]
      else:
        try:
          i = self._unhashable_items.index(key)
          if self._unhashable_counts[i] > 1:
            self._unhashable_counts[i] -= 1
          else:
            del self._unhashable_counts[i]
            del self._unhashable_items[i]
        except ValueError:
          pass


class _IterableSubject(_DefaultSubject):
  """Subject for things that are iterable.

  When making assertions with the ContainsAll...() or ContainsExactly...()
  methods, predicated with .InOrder(), use caution when mixing ordered iterables
  with ones that do not have a defined order. For example, while these
  assertions will always succeed:
    AssertThat((1, 2, 3)).ContainsAllIn((1, 3)).InOrder()
    AssertThat((1, 2, 3)).ContainsExactlyElementsIn([1, 2, 3]).InOrder()
    AssertThat(collections.OrderedDict(((1, 2), (3, 4)))
              ).ContainsExactly((1, 3)).InOrder()

  these assertions *may or may not* succeed:
    AssertThat((1, 2, 3)).ContainsAllIn(set([1, 3])).InOrder()
    AssertThat(set([1, 2, 3])).ContainsExactlyElementsIn((1, 2, 3)).InOrder()
    AssertThat({1: 2, 3: 4}).ContainsExactly(1, 3).InOrder()

  whereas they would always succeed without the .InOrder().
  """

  @asserts_truth
  def IsEqualTo(self, other):
    try:
      if (type(self._actual) is type(other)
          and not isinstance(self._actual, type(mock.call))
          and not isinstance(self._actual, six.string_types)
          and not isinstance(other, six.string_types)):
        if isinstance(self._actual, collections_abc.Sequence):
          return self.ContainsExactlyElementsIn(other).InOrder()
        return self.ContainsExactlyElementsIn(other)
    except (AttributeError, TypeError):
      pass

    return super(_IterableSubject, self).IsEqualTo(other)

  @asserts_truth
  def HasSize(self, size):
    actual_length = len(self._actual)
    if actual_length != size:
      self._FailWithBadResults('has a size of', size, 'is', actual_length)

  @asserts_truth
  def IsEmpty(self):
    if self._actual:
      self._FailWithProposition('is empty')

  @asserts_truth
  def IsNotEmpty(self):
    if not self._actual:
      self._FailWithProposition('is not empty')

  @asserts_truth
  def Contains(self, element):
    if element not in self._actual:
      self._FailWithSubject('should have contained <{0!r}>'.format(element))

  @asserts_truth
  def DoesNotContain(self, element):
    if element in self._actual:
      self._FailWithSubject(
          'should not have contained <{0!r}>'.format(element))

  @asserts_truth
  def ContainsNoDuplicates(self):
    """Asserts that this subject contains no two elements that are the same."""
    # Dictionaries and Sets have unique members by definition; avoid iterating.
    if isinstance(self._actual, (collections_abc.Mapping, collections_abc.Set)):
      return
    duplicates = []
    entries = set()
    for i in self._actual:
      if i in entries:
        duplicates.append(i)
      entries.add(i)
    if duplicates:
      self._FailWithSubject(
          'has the following duplicates: <{0}>'.format(duplicates))

  @asserts_truth
  def ContainsAllIn(self, expected):
    return self._ContainsAll('contains all elements in', expected)

  @asserts_truth
  def ContainsAllOf(self, *expected):
    return self._ContainsAll('contains all of', expected)

  @asserts_truth
  def ContainsAnyIn(self, expected):
    return self._ContainsAny('contains any element in', expected)

  @asserts_truth
  def ContainsAnyOf(self, *expected):
    return self._ContainsAny('contains any of', expected)

  @asserts_truth
  def ContainsExactly(self, *expected):
    expecting_single_iterable = (
        len(expected) == 1 and _IsIterable(expected)
        and not isinstance(expected[0], six.string_types))
    return self._ContainsExactlyElementsIn(
        expected, warn_elements_in=expecting_single_iterable)

  @asserts_truth
  def ContainsExactlyElementsIn(self, expected):
    return self._ContainsExactlyElementsIn(expected)

  @asserts_truth
  def ContainsNoneIn(self, excluded):
    self._ContainsNone('contains no elements in', excluded)

  @asserts_truth
  def ContainsNoneOf(self, *excluded):
    self._ContainsNone('contains none of', excluded)

  @asserts_truth
  def IsOrdered(self):
    self.IsOrderedAccordingTo(Cmp)

  @asserts_truth
  def IsOrderedAccordingTo(self, comparator):
    self._PairwiseCheck(lambda a, b: comparator(a, b) <= 0, strict=False)

  @asserts_truth
  def IsStrictlyOrdered(self):
    self.IsStrictlyOrderedAccordingTo(Cmp)

  @asserts_truth
  def IsStrictlyOrderedAccordingTo(self, comparator):
    self._PairwiseCheck(lambda a, b: comparator(a, b) < 0, strict=True)

  def _ContainsAll(self, verb, expected):
    """Determines if the subject contains all the expected elements.

    Helper function for ContainsAllIn() and ContainsAllOf().

    Args:
      verb: string describing how the expected elements should be contained.
      expected: iterable of objects that should be contained in the subject.

    Returns:
      If the subject does contain all the expected elements, returns an
      _Ordered predicate on which .InOrder() can be subsequently called.

    Raises:
      TruthAssertionError: the subject is missing any of the expected elements.
    """
    actual_list = list(self._actual)
    missing = _DuplicateCounter()
    actual_not_in_order = set()
    ordered = True

    # Step through the expected elements.
    for i in expected:
      try:
        index = actual_list.index(i)
        # Drain all the elements before that element into actual_not_in_order.
        for _ in six.moves.xrange(index):
          actual_element = actual_list.pop(0)
          if (_IsHashable(actual_element)
              and isinstance(actual_not_in_order, collections_abc.Set)):
            actual_not_in_order.add(actual_element)
          else:
            if isinstance(actual_not_in_order, collections_abc.Set):
              actual_not_in_order = list(actual_not_in_order)
            if actual_element not in actual_not_in_order:
              actual_not_in_order.append(actual_element)
        # And remove the element from the actual_list.
        actual_list.pop(0)
      # The expected value was not in the actual list.
      except ValueError:
        if (not _IsHashable(i)
            and isinstance(actual_not_in_order, collections_abc.Set)):
          actual_not_in_order = list(actual_not_in_order)
        if i in actual_not_in_order:
          actual_not_in_order.remove(i)
          # If it was in actual_not_in_order, we're not in order.
          ordered = False
        else:
          # It is not in actual_not_in_order, we're missing an expected element.
          missing.Increment(i)

    # If we have any missing expected elements, fail.
    if missing:
      self._FailWithBadResults(verb, expected, 'is missing', missing)

    if ordered:
      return _InOrder()
    else:
      return _NotInOrder(
          self._actual, 'contains all elements in order', expected)

  def _ContainsAny(self, verb, expected):
    """Determines if the subject contains any of the expected elements.

    Helper function for ContainsAnyIn() and ContainsAnyOf().

    Args:
      verb: string describing how the expected elements should be contained.
      expected: iterable of objects that should be contained in the subject.

    Returns:
      None if the subject contains any of the expected elements.

    Raises:
      TruthAssertionError: the subject is missing all of the expected elements.
    """
    # Optimize for space when there is exactly 1 expected element.
    if len(expected) == 1 and expected[0] in self._actual:
      return

    # Otherwise we know we have to check "in" self._actual at least twice,
    # so optimize for time by converting it to a set first, if possible.
    if expected:
      try:
        actual_set = set(self._actual)
      except TypeError:
        actual_set = self._actual
      for i in expected:
        if i in actual_set:
          return
    self._FailComparingValues(verb, expected)

  def _ContainsExactlyElementsIn(self, expected, warn_elements_in=False):
    """Determines if the subject contains exactly the expected elements.

    Helper function for ContainsExactly() and ContainsExactlyElementsIn().

    Args:
      expected: iterable of objects that should be contained in the subject.
      warn_elements_in: boolean, default False. If True, and the assertion
          fails, and the developer invoked ContainsExactly() with a single
          iterable, warn that this usage is error-prone.

    Returns:
      If the subject does contain exactly the expected elements, returns an
      _Ordered predicate on which .InOrder() can be subsequently called.

    Raises:
      TruthAssertionError: the subject is missing any of the expected elements,
          or the subject contains any element not in the expected elements.
    """
    if not expected:
      if self._actual:
        self._FailWithProposition('is empty')
      return _InOrder()

    missing = _DuplicateCounter()
    extra = _DuplicateCounter()
    actual_iter = iter(self._actual)
    expected_iter = iter(expected)

    warning = ''
    if warn_elements_in:
      warning = (
          ' Passing a single iterable to ContainsExactly(*expected) is often'
          ' not the correct thing to do. Did you mean to call'
          ' ContainsExactlyElementsIn(Iterable) instead?')

    while True:
      # Step through both iterators comparing elements pairwise.
      try:
        actual_element = next(actual_iter)
      except StopIteration:
        break

      try:
        expected_element = next(expected_iter)
      except StopIteration:
        extra.Increment(actual_element)
        break

      # As soon as we encounter a pair of elements that differ, we know that
      # InOrder() cannot succeed, so we can check the rest of the elements
      # more normally. Since any previous pairs of elements we iterated
      # over were equal, they have no effect on the result now.
      if actual_element != expected_element:
        # Missing elements; elements that are not missing will be removed.
        missing.Increment(expected_element)
        for m in expected_iter:
          missing.Increment(m)

        # Remove all actual elements from missing, and add any that weren't
        # in missing to extra.
        if actual_element in missing:
          missing.Decrement(actual_element)
        else:
          extra.Increment(actual_element)
        for e in actual_iter:
          if e in missing:
            missing.Decrement(e)
          else:
            extra.Increment(e)

        # Fail if there are either missing or extra elements.

        if missing:
          if extra:
            # Subject is missing required elements and has extra elements.
            self._FailWithProposition(
                'contains exactly <{0!r}>.'
                ' It is missing <{1}> and has unexpected items <{2}>'
                .format(expected, missing, extra),
                suffix=warning)
          else:
            self._FailWithBadResults(
                'contains exactly', expected, 'is missing', missing,
                suffix=warning)
        if extra:
          self._FailWithBadResults(
              'contains exactly', expected, 'has unexpected items', extra,
              suffix=warning)

        # The iterables were not in the same order, InOrder() can just fail.
        return _NotInOrder(
            self._actual, 'contains exactly these elements in order', expected)

    # We must have reached the end of one of the iterators without finding any
    # pairs of elements that differ. If the actual iterator still has elements,
    # they're extras. If the required iterator has elements, they're missing.
    for e in actual_iter:
      extra.Increment(e)
    if extra:
      self._FailWithBadResults(
          'contains exactly', expected, 'has unexpected items', extra,
          suffix=warning)

    for m in expected_iter:
      missing.Increment(m)
    if missing:
      self._FailWithBadResults(
          'contains exactly', expected, 'is missing', missing,
          suffix=warning)

    # If neither iterator has elements, we reached the end and the elements
    # were in order, so InOrder() can just succeed.
    return _InOrder()

  def _ContainsNone(self, fail_verb, excluded):
    """Determines if the subject contains none of the excluded elements.

    Helper function for ContainsNoneIn() and ContainsNoneOf().

    Args:
      fail_verb: string describing how the excluded elements should be excluded.
      excluded: iterable of objects that should not be contained in the subject.

    Returns:
      None if the subject contains none of the expected elements.

    Raises:
      TruthAssertionError: the subject contains any of the excluded elements.
    """
    present = []
    # Optimize for space when there is exactly 1 excluded element.
    if len(excluded) == 1:
      if excluded[0] in self._actual:
        present.extend(excluded)

    # Otherwise we know we have to check "in" self._actual at least twice,
    # so optimize for time by converting it to a set first, if possible.
    elif excluded:
      try:
        actual_set = set(self._actual)
      except TypeError:
        actual_set = self._actual
      for i in excluded:
        if i in actual_set:
          present.append(i)
    if present:
      self._FailWithBadResults(fail_verb, excluded, 'contains', present)

  def _PairwiseCheck(self, pair_comparator, strict=False):
    """Iterates over this subject and compares adjacent elements.

    For example, compares element 0 with element 1, 1 with 2, ... n-1 with n.

    Args:
      pair_comparator: A function accepting two arguments. If the arguments are
          ordered as expected, the function should return True, otherwise False.
      strict: whether the pair comparator function is strict.
    """
    i = iter(self._actual)
    try:
      prev = next(i)
      while True:
        current = next(i)
        if not pair_comparator(prev, current):
          strictly = 'strictly ' if strict else ''
          self._FailComparingValues(
              'is {0}ordered'.format(strictly), (prev, current))
        prev = current
    except StopIteration:
      pass


class _Ordered(_EmptySubject):
  """Additional abstract assertion adverb allowing an arrangement aspect."""

  def __init__(self):
    super(_Ordered, self).__init__(None)
    self._Resolve()

  def InOrder(self):
    raise NotImplementedError()


class _InOrder(_Ordered):
  """Adverb for an iterable that is already known to be in order."""

  @asserts_truth
  def InOrder(self):
    pass


class _NotInOrder(_Ordered):
  """Adverb for an iterable that is already known to be out of order."""

  def __init__(self, actual, check, expected):
    super(_NotInOrder, self).__init__()
    self._actual = actual
    self._check = check
    self._expected = expected

  @asserts_truth
  def InOrder(self):
    self._FailComparingValues(self._check, self._expected)


class _ComparableIterableSubject(_ComparableSubject, _IterableSubject):
  """Subject for things that are both comparable and iterable, like lists."""


class _DictionarySubject(_ComparableIterableSubject):
  """Subject for dictionaries.

  Accepts primitive dictionaries and any subclasses thereof, such as
  collections.defaultdict and collections.OrderedDict.

  When evaluating a defaultdict, values are not deemed present unless a
  corresponding key is also present. These assertions fail:
    AssertThat(collections.defaultdict(int)).ContainsItem('key', 0)
    AssertThat(collections.defaultdict(list)).ContainsItem('key', [])

  When iterating over both the subject and the expected values, the default
  iteration order is used. If you require orderedness, ensure that both the
  subject and the expected value are ordered. For example, while this assertion
  always succeeds:
    AssertThat(collections.OrderedDict(((1, 2), (3, 4)))
              ).ContainsExactly(1, 2, 3, 4).InOrder()

  these assertions *may or may not* succeed:
    AssertThat(collections.OrderedDict(((1, 2), (3, 4)))
              ).ContainsExactlyItemsIn({1: 2, 3: 4}).InOrder()
    AssertThat({1: 2, 3: 4})).ContainsExactly(1, 2, 3, 4).InOrder()

  whereas they would always succeed without the .InOrder().

  The warnings about orderedness in _IterableSubject also apply.
  """

  @asserts_truth
  def IsEqualTo(self, other):
    if type(self._actual) is type(other):
      if isinstance(self._actual, collections.OrderedDict):
        return self.ContainsExactlyItemsIn(other).InOrder()
      return self.ContainsExactlyItemsIn(other)

    return super(_DictionarySubject, self).IsEqualTo(other)

  @asserts_truth
  def ContainsKey(self, key):
    if key not in self._actual:
      self._FailWithProposition('contains key <{0}>'.format(key))

  @asserts_truth
  def DoesNotContainKey(self, key):
    if key in self._actual:
      self._FailWithProposition('does not contain key <{0}>'.format(key))

  @asserts_truth
  def ContainsItem(self, key, value):
    """Assertion that the subject contains the key mapping to the value."""
    if key in self._actual:
      if self._actual[key] == value:
        return
      else:
        self._FailWithProposition(
            'contains item <{0!r}>.'
            ' However, it has a mapping from <{1!r}> to <{2!r}>'
            .format((key, value), key, self._actual[key]))

    other_keys = []
    for k, v in six.iteritems(self._actual):
      if v == value:
        other_keys.append(k)
    if other_keys:
      self._FailWithProposition(
          'contains item <{0!r}>.'
          ' However, the following keys are mapped to <{1!r}>: {2!r}'
          .format((key, value), value, other_keys))

    self._FailWithProposition('contains item <{0!r}>'.format((key, value)))

  @asserts_truth
  def DoesNotContainItem(self, key, value):
    if key in self._actual and self._actual[key] == value:
      self._FailWithProposition(
          'does not contain item <{0!r}>'.format((key, value)))

  @asserts_truth
  def ContainsExactly(self, *items):
    if len(items) % 2:
      raise ValueError(
          'There must be an equal number of key/value pairs'
          ' (i.e., the number of key/value parameters ({0}) must be even).'
          .format(len(items)))
    expected = collections.OrderedDict()
    for i in six.moves.xrange(0, len(items), 2):
      expected[items[i]] = items[i + 1]
    return self.ContainsExactlyItemsIn(expected)

  @asserts_truth
  def ContainsExactlyItemsIn(self, expected):
    return AssertThat(self._actual.items()).ContainsExactly(*expected.items())

  # Method aliases when translating Java's Map.Entry to Python's items.
  # pylint: disable=invalid-name
  ContainsEntry = ContainsItem
  DoesNotContainEntry = DoesNotContainItem
  ContainsExactlyEntriesIn = ContainsExactlyItemsIn
  # pylint: enable=invalid-name


class _NumericSubject(_ComparableSubject):
  """Subject for all types of numbers--int, long, float, and complex."""

  @asserts_truth
  def IsZero(self):
    if self._actual != 0:
      self._FailWithProposition('is zero')

  @asserts_truth
  def IsNonZero(self):
    if self._actual == 0:
      self._FailWithProposition('is non-zero')

  @asserts_truth
  def IsFinite(self):
    if math.isinf(self._actual) or math.isnan(self._actual):
      self._FailWithSubject('should have been finite')

  @asserts_truth
  def IsNotFinite(self):
    if not math.isinf(self._actual) and not math.isnan(self._actual):
      self._FailWithSubject('should not have been finite')

  @asserts_truth
  def IsPositiveInfinity(self):
    self.IsEqualTo(POSITIVE_INFINITY)

  @asserts_truth
  def IsNegativeInfinity(self):
    self.IsEqualTo(NEGATIVE_INFINITY)

  @asserts_truth
  def IsNan(self):
    if not math.isnan(self._actual):
      self._FailComparingValues('is equal to', NAN)

  @asserts_truth
  def IsNotNan(self):
    if math.isnan(self._actual):
      self._FailWithSubject('should not have been <{0}>'.format(NAN))

  def IsWithin(self, tolerance):
    return _TolerantNumericSubject(self._actual, tolerance, True)

  def IsNotWithin(self, tolerance):
    return _TolerantNumericSubject(self._actual, tolerance, False)


class _TolerantNumericSubject(_EmptySubject):
  """Subject for a number that must be (or not be) in a window of tolerance."""

  def __init__(self, actual, tolerance, within):
    super(_TolerantNumericSubject, self).__init__(actual)
    self._tolerance = tolerance
    self._within = within

  @asserts_truth
  def Of(self, expected):
    self._CheckTolerance()
    tolerably_equal = abs(self._actual - expected) <= self._tolerance
    not_within = '' if self._within else 'not '
    if self._within != tolerably_equal:
      self._FailWithSubject(
          'and <{0}> should {1}have been within <{2}> of each other'
          .format(expected, not_within, self._tolerance))

  def _CheckTolerance(self):
    if math.isnan(self._tolerance):
      raise ValueError('tolerance cannot be <{0}>'.format(NAN))
    if self._tolerance < 0.0:
      raise ValueError('tolerance cannot be negative')
    if math.isinf(self._tolerance):
      raise ValueError('tolerance cannot be positive infinity')


class _StringSubject(_ComparableIterableSubject):
  """Subject for all types of strings--basic and Unicode."""

  def _GetSubject(self):
    if self._actual and '\n' in self._actual:
      return 'actual {0}'.format(self._name) if self._name else 'actual'
    return super(_StringSubject, self)._GetSubject()

  @asserts_truth
  def IsEqualTo(self, expected):
    # Use unified diff strategy when comparing multiline strings.
    if (isinstance(expected, six.string_types)
        and '\n' in self._actual and '\n' in expected):
      if self._actual != expected:
        pretty_diff_list = difflib.ndiff(
            self._actual.splitlines(True), expected.splitlines(True))
        pretty_diff = '\n'.join(repr(s)[1:-1] for s in pretty_diff_list)
        self._FailWithProposition(
            'is equal to expected, found diff:\n{0}'.format(pretty_diff))
    else:
      super(_StringSubject, self).IsEqualTo(expected)

  @asserts_truth
  def HasLength(self, expected):
    actual_length = len(self._actual)
    if actual_length != expected:
      self._FailWithProposition(
          'has a length of {0}. It is {1}'.format(expected, actual_length))

  @asserts_truth
  def StartsWith(self, prefix):
    if not self._actual.startswith(prefix):
      self._FailComparingValues('starts with', prefix)

  @asserts_truth
  def EndsWith(self, suffix):
    if not self._actual.endswith(suffix):
      self._FailComparingValues('ends with', suffix)

  @asserts_truth
  def Matches(self, regex):
    r = re.compile(regex)
    if not r.match(self._actual):
      self._FailWithProposition('matches <{0}>'.format(r.pattern))

  @asserts_truth
  def DoesNotMatch(self, regex):
    r = re.compile(regex)
    if r.match(self._actual):
      self._FailWithProposition('fails to match <{0}>'.format(r.pattern))

  @asserts_truth
  def ContainsMatch(self, regex):
    r = re.compile(regex)
    if not r.search(self._actual):
      self._FailWithSubject(
          'should have contained a match for <{0}>'.format(r.pattern))

  @asserts_truth
  def DoesNotContainMatch(self, regex):
    r = re.compile(regex)
    if r.search(self._actual):
      self._FailWithSubject(
          'should not have contained a match for <{0}>'.format(r.pattern))


class _NamedMockSubject(_DefaultSubject):
  """Subject for functions mocked by "mock", which set their "name" property."""

  def __init__(self, actual):
    super(_NamedMockSubject, self).__init__(actual)
    if hasattr(actual, '_mock_name'):
      self.Named(getattr(actual, '_mock_name') or 'mock')
    else:
      self.Named('mock')


class _MockSubject(_NamedMockSubject):
  """Subject for functions mocked by "mock".

  Conversion recipes from mock to Truth:

    mock_func.assert_called() ->
      AssertThat(mock_func).WasCalled()

    mock_func.assert_not_called() ->
      AssertThat(mock_func).WasNotCalled()

    mock_func.assert_called_once() ->
      AssertThat(mock_func).WasCalled().Once()

    mock_func.assert_called_with(*a, **k) ->
      AssertThat(mock_func).WasCalled().LastWith(*a, **k)

    mock_func.assert_called_once_with(*a, **k) ->
      AssertThat(mock_func).WasCalled().Once().With(*a, **k)

    mock_func.assert_has_calls(calls, any_order=True) ->
      AssertThat(mock_func).HasCalls(calls)

    mock_func.assert_has_calls(calls, any_order=False) ->
      AssertThat(mock_func).HasCalls(calls).InOrder()

    mock_func.assert_any_call(*a, **k) ->
      AssertThat(mock_func).WasCalled().With(*a, **k)

  Note that the WasCalled().Once().With(...) and WasCalled().With(...).Once()
  assertions are subtly different. WasCalled().Once().With(...) asserts that the
  function was called one time ever, and that one time it was called, it was
  passed those arguments. WasCalled().With(...).Once() asserts that the function
  was passed those arguments exactly once, but it is permitted to have been
  called with other, irrelevant arguments. Thus, WasCalled().Once().With(...)
  is the stricter assertion. Consider using HasExactlyCalls() for more clarity.

  Mock subjects can also be used to make value assertions. For example:

    AssertThat(actual_mock).IsAnyOf(mock1, mock2)
    AssertThat(actual_mock).IsEqualTo(expected_mock)
    AssertThat(actual_mock).IsSameAs(expected_mock)
  """

  @asserts_truth
  def WasCalled(self):
    if not self._actual.call_count:
      self._Fail(
          "Expected '{0}' to have been called, but it was not.\nAll calls: {1}"
          .format(self.name, self._actual.mock_calls))
    return _MockCalledSubject(self._actual)

  @asserts_truth
  def WasNotCalled(self):
    if self._actual.call_count:
      self._Fail(
          "Expected '{0}' not to have been called, but it was called {1}.\n"
          'All calls: {2}'
          .format(self.name, _DescribeTimes(self._actual.call_count),
                  self._actual.mock_calls))

  @asserts_truth
  def HasCalls(self, *calls, **kwargs):
    """Assert that the mocked function was called with all the given calls.

    Args:
      *calls: iterable of mock.call objects. Developers may also pass a single
          iterable of mock.call objects, for compatibility with mock's
          assert_has_calls() method, although this form is not preferred.
      **kwargs: optional parameters. The only recognized parameter is any_order:
          If any_order=True, the assertion succeeds if the mocked function was
              called with all the given calls, regardless of the call order.
          If any_order=False, the assertion succeeds if the mocked function was
              called with all of the given calls in the given order.
          If any_order is omitted, it behaves like any_order=True. This is the
              preferred way of calling HasCalls(). Developers who wish to
              enforce an order should call InOrder() on the returned predicate.
              If the order is unimportant, simply omit the InOrder() call.
              This is an intentional divergence from the mock library's syntax.

    Returns:
      If any_order is True or omitted, and the mocked function was called all of
          with the expected calls, returns an _Ordered predicate on which
          .InOrder() can be subsequently called.
      If any_order=False, invokes the InOrder() predicate and returns its value.

    Raises:
      TruthAssertionError: the mocked function is missing any of the expected
          calls.
    """
    # If the caller passed an iterable of mock.call objects, expand them.
    # mock.call objects are themselves iterable, hence the third condition.
    if (len(calls) == 1 and _IsIterable(calls[0])
        # pylint: disable=protected-access
        and not isinstance(calls[0], mock._Call)):
        # pylint: enable=protected-access
      calls = calls[0]

    contains_all = AssertThat(self._actual.mock_calls).ContainsAllIn(calls)
    any_order = kwargs.get('any_order')
    if any_order or any_order is None:
      return contains_all
    return contains_all.InOrder()

  @asserts_truth
  def HasExactlyCalls(self, *calls):
    """Assert that the mocked function was called with exactly the given calls.

    Args:
      *calls: iterable of mock.call objects. Developers may also pass a single
          iterable of mock.call objects, for compatibility with mock's
          assert_has_calls() method, although this form is not preferred.

    Returns:
      If the mocked function was called exactly with the expected calls, returns
      an _Ordered predicate on which .InOrder() can be subsequently called.

    Raises:
      TruthAssertionError: the mocked function is missing any of the expected
          calls, or it contains any call not in the expected calls.
    """
    # If the caller passed an iterable of mock.call objects, expand them.
    # mock.call objects are themselves iterable, hence the third condition.
    if (len(calls) == 1 and _IsIterable(calls[0])
        # pylint: disable=protected-access
        and not isinstance(calls[0], mock._Call)):
        # pylint: enable=protected-access
      calls = calls[0]

    return AssertThat(self._actual.mock_calls).ContainsExactlyElementsIn(calls)


class _MockCalledSubject(_NamedMockSubject):
  """Subject for a mock already asserted [not] to have been called."""

  def __init__(self, actual):
    super(_MockCalledSubject, self).__init__(actual)
    self._Resolve()      # Allow AssertThat(m).WasCalled().

  @asserts_truth
  def Once(self):
    return self.Times(1)

  @asserts_truth
  def Times(self, expected):
    """Asserts that the mock was called an expected number of times."""
    if self._actual.call_count != expected:
      self._Fail(
          "Expected '{0}' to have been called {1}. Called {2}.\n"
          "All calls: {3}"
          .format(self.name,
                  _DescribeTimes(expected),
                  _DescribeTimes(self._actual.call_count),
                  self._actual.mock_calls))
    return self

  @asserts_truth
  def With(self, *args, **kwargs):
    call = mock.call(*args, **kwargs)
    if call not in self._actual.mock_calls:
      self._Fail(
          "Expected '{0}' to have been called with {1}, but it was not.\n"
          'All calls: {2}'
          .format(self.name, call, self._actual.mock_calls))
    return _MockCalledWithSubject(self._actual, call)

  @asserts_truth
  def LastWith(self, *args, **kwargs):
    if (self._actual.call_args is None
        or self._actual.call_args != (args, kwargs)):
      self._Fail(
          "Expected '{0}' to have last been called with {1}, but it was not.\n"
          'All calls: {2}'
          .format(self.name, mock.call(*args, **kwargs),
                  self._actual.mock_calls))


class _MockCalledWithSubject(_NamedMockSubject):
  """Subject for a mock that was called with a specified set of arguments."""

  def __init__(self, actual, call):
    super(_MockCalledWithSubject, self).__init__(actual)
    self._call = call
    self._Resolve()      # Allow AssertThat(m).WasCalled().With(...).

  @asserts_truth
  def Once(self):
    self.Times(1)

  @asserts_truth
  def Times(self, expected):
    actual_call_count = self._actual.mock_calls.count(self._call)
    if actual_call_count != expected:
      self._Fail(
          "Expected '{0}' to have been called with {1} {2}. Called {3}.\n"
          'All calls: {4}'
          .format(self.name, self._call,
                  _DescribeTimes(expected),
                  _DescribeTimes(actual_call_count),
                  self._actual.mock_calls))


class _NoneSubject(
    _BooleanSubject,
    _DictionarySubject,
    _ExceptionClassSubject,
    _ExceptionSubject,
    _MockSubject,
    _NumericSubject,
    _StringSubject):
  """Subject for comparing None.

  This is a catch-all subject which defines every possible predicate.
  It should transitively inherit from every other subject in this module.

  None is like null in Java: all comparisons to None are valid, although the
  only thing that None will be equivalent to is None.

  None can never contain anything. For example:
    AssertThat(Func()).ContainsExactly(1, 4, 7).InOrder()
  will compile and run, but it raises an assertion if Func() returns None.

  In Python 2, None compares less than every other thing, except None itself.
  None is less than NaN, and it is less than negative infinity. Therefore, use
  caution when a function might return None. This assertion succeeds:
    AssertThat(Func()).IsLessThan(0)
  whether Func() returns a negative number or None. Instead, first check the
  None-ness of the return value with IsNone() or IsNotNone() before performing
  an inequality assertion.

  In Python 3, None is no longer comparable using < > <= >= . This module
  detects the version of Python and compares or fails appropriately, rather than
  allowing Python 3's TypeError to bubble up.
  """

  @asserts_truth
  def IsEqualTo(self, other):
    return _DefaultSubject.IsEqualTo(self, other)

  @asserts_truth
  def __getattribute__(self, name):
    if (name.startswith('_') or
        name[0] == name[0].lower() or
        hasattr(_BooleanSubject, name) or
        (six.PY2 and
         hasattr(_NumericSubject, name) and
         name not in ('IsWithin', 'IsNotWithin'))):
      return object.__getattribute__(self, name)

    self._Fail(
        'Invalid operation on {0} subject: <{1}>.'
        ' Check that the actual value of the subject is not None,'
        ' or AssertThat the subject IsNone()/IsNotNone()'
        .format(self._actual, name))


# Tight bindings of object superclasses to subject constructors.
# No key in this dictionary should be a subclass of any other key.
# This dictionary must come last because its values are classes defined above.
_TYPE_CONSTRUCTORS = {
    BaseException: _ExceptionSubject,
    bool: _BooleanSubject,
    collections_abc.Mapping: _DictionarySubject,
    mock.NonCallableMock: _MockSubject,
    type(None): _NoneSubject
}
for t in six.string_types:
  _TYPE_CONSTRUCTORS[t] = _StringSubject
for t in six.class_types:
  if t is not type:
    _TYPE_CONSTRUCTORS[t] = _ClassSubject


# We really want to dissuade anyone from calling _CheckUnresolved().
# pylint: disable=protected-access
atexit.register(_EmptySubject._CheckUnresolved)
# pylint: enable=protected-access
