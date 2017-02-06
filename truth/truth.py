# Copyright 2017 Google Inc.
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
  AssertThat = truth.AssertThat

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
    |     `-- _MockAssertionConverter
    |           |-- _MockSubject
    |           `-- _MockCalledSubject
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

import atexit
import collections
import contextlib
import inspect
import math
import numbers
import re
import sys
import threading
import types

from mock import mock

# All these attributes must be present for an object to be deemed comparable.
_COMPARABLE_ATTRS = frozenset(
    '__{0}__'.format(attr) for attr in ('lt', 'le', 'gt', 'ge'))

# Special numeric concepts.
POSITIVE_INFINITY = float('inf')
NEGATIVE_INFINITY = float('-inf')
NAN = float('nan')

# Python 2/3 compatibility.
_PYTHON2 = sys.version_info.major < 3
BaseString = basestring if _PYTHON2 else str
Cmp = cmp if _PYTHON2 else lambda a, b: (a > b) - (a < b)
ItemsOf = lambda d: d.iteritems() if _PYTHON2 else d.items()
NoneType = types.NoneType if _PYTHON2 else type(None)
TypeType = types.TypeType if _PYTHON2 else type
Range = xrange if _PYTHON2 else range


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

  # All types descend from TypeType, so check if target is a type itself first.
  if type(target) is TypeType:
    if issubclass(target, BaseException):
      return _ExceptionClassSubject(target)
    return _ClassSubject(target)

  for super_type, subject_class in ItemsOf(_TYPE_CONSTRUCTORS):
    # Must use issubclass() and not isinstance(), because mocked functions
    # override their __class__. See mock._is_instance().
    if issubclass(type(target), super_type):
      return subject_class(target)

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


def _IsIterable(target):
  """Returns True if the target is iterable."""
  return isinstance(target, collections.Iterable)


def _IsNumeric(target):
  """Returns True if the target is a number."""
  return isinstance(target, numbers.Number)


class _EmptySubject(object):
  """Base class for all subjects.

  The empty subject cannot test anything; it provides only methods for failing.
  """

  _unresolved_subjects = set()
  _unresolved_subjects_lock = threading.Lock()

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

  def _FailComparingValues(self, verb, other):
    self._FailWithProposition('{0} <{1!r}>'.format(verb, other))

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

  def IsEqualTo(self, other):
    if self._actual != other:
      self._FailComparingValues('is equal to', other)

  def IsNotEqualTo(self, other):
    if self._actual == other:
      self._FailComparingValues('is not equal to', other)

  def IsNone(self):
    if self._actual is not None:
      self._FailWithProposition('is None')

  def IsNotNone(self):
    if self._actual is None:
      self._FailWithProposition('is not None')

  def IsIn(self, iterable):
    if self._actual not in iterable:
      self._FailComparingValues('is equal to any of', iterable)

  def IsNotIn(self, iterable):
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

  def IsAnyOf(self, *iterable):
    return self.IsIn(iterable)

  def IsNoneOf(self, *iterable):
    return self.IsNotIn(iterable)

  def IsInstanceOf(self, cls):
    if not isinstance(self._actual, cls):
      self._FailWithBadResults(
          'is an instance of', cls, 'is an instance of', type(self._actual))

  def IsNotInstanceOf(self, cls):
    if isinstance(self._actual, cls):
      self._FailWithSubject(
          'expected not to be an instance of {0}, but was'.format(cls))

  def IsSameAs(self, other):
    if self._actual is not other:
      self._FailComparingValues('is the same instance as', other)

  def IsNotSameAs(self, other):
    if self._actual is other:
      self._FailComparingValues('is not the same instance as', other)

  def IsTruthy(self):
    if not self._actual:
      self._FailWithProposition('is truthy')

  def IsFalsy(self):
    if self._actual:
      self._FailWithProposition('is falsy')

  def IsTrue(self):
    suffix = ''
    if self._actual:
      suffix = (' However, it is truthy.'
                ' Did you mean to call IsTruthy() instead?')
    self._FailWithProposition('is True', suffix=suffix)

  def IsFalse(self):
    suffix = ''
    if not self._actual:
      suffix = ' However, it is falsy. Did you mean to call IsFalsy() instead?'
    self._FailWithProposition('is False', suffix=suffix)

  # Recognize alternate spelling.
  IsFalsey = IsFalsy

  def HasAttribute(self, attr):
    if not hasattr(self._actual, attr):
      self._FailComparingValues('has attribute', attr)

  def DoesNotHaveAttribute(self, attr):
    if hasattr(self._actual, attr):
      self._FailComparingValues('does not have attribute', attr)

  def IsCallable(self):
    if not callable(self._actual):
      self._FailWithProposition('is callable')

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

  def __exit__(self, exc_type, exc_val, exc_tb):
    """This method must merely exist to be recognized as a context."""


class _ExceptionSubject(_DefaultSubject, _UnresolvedContextMixin):
  """Subject for exceptions (i.e., instances of BaseException)."""

  def HasMessage(self, expected):
    AssertThat(self._GetActualMessage()).IsEqualTo(expected)

  def HasMessageThat(self):
    return AssertThat(self._GetActualMessage())

  def HasArgsThat(self):
    return AssertThat(self._actual.args)

  @contextlib.contextmanager
  def IsRaised(self):
    """Asserts that an exception matching this subject is raised.

    The raised exception must be the same type as (or a subclass of) this
    subject's. The raised exception's "message" and "args" attributes must
    match this subject's exactly. As this is a fairly strict match,
    _ExceptionClassSubject.IsRaised() may be easier to use.

    Yields:
      None
    """
    try:
      yield
    except type(self._actual) as e:
      if hasattr(self._actual, 'message'):
        AssertThat(e).HasMessage(self._GetActualMessage())
      AssertThat(e).HasArgsThat().ContainsExactlyElementsIn(
          self._actual.args).InOrder()
    except BaseException as e:
      self._FailWithSubject(
          'should have been raised, but caught <{0!r}>'.format(e))
    else:
      self._FailWithSubject('should have been raised, but was not')

  def _GetActualMessage(self):
    """Returns the "message" portion of an exception.

    Many Python 2 exceptions have a "message" attribute, so return that directly
    in Python 2. However, this attribute is never present in Python 3, so return
    the first argument passed to the exception instance as the message.

    Returns:
      String
    """
    if _PYTHON2:
      return self._actual.message
    return self._actual.args[0] if self._actual.args else ''


class _BooleanSubject(_DefaultSubject):
  """Subject for booleans."""

  def IsTrue(self):
    if self._actual is not True:
      self._FailWithSubject(
          'was expected to be True, but was {0}'.format(self._actual))

  def IsFalse(self):
    if self._actual is not False:
      self._FailWithSubject(
          'was expected to be False, but was {0}'.format(self._actual))


class _ClassSubject(_DefaultSubject):
  """Subject for classes."""

  def IsSubclassOf(self, other):
    """Fails if this is not the same as, or a subclass of, the given class."""
    if not issubclass(self._actual, other):
      self._FailComparingValues('is a subclass of', other)


class _ExceptionClassSubject(_ClassSubject, _UnresolvedContextMixin):
  """Subject for exception classes (i.e., subclasses of BaseException)."""

  @contextlib.contextmanager
  def IsRaised(self, matching=None):
    """Asserts that an exception matching this subject is raised.

    The raised exception must be the same type as (or a subclass of) this
    subject's.

    Args:
      matching: string or regex object. If present, the raised exception's
          "message" attribute must contain this value. If omitted, the raised
          exception's message is not checked.

    Yields:
      None
    """
    try:
      yield
    except self._actual as e:
      if matching is not None:
        AssertThat(e).HasMessageThat().ContainsMatch(matching)
    except BaseException as e:
      self._FailWithSubject(
          'should have been raised, but caught <{0!r}>'.format(e))
    else:
      self._FailWithSubject('should have been raised, but was not')


class _ComparableSubject(_DefaultSubject):
  """Subject for things that are comparable using the < > <= >= operators."""

  def IsAtLeast(self, other):
    self._CheckNone('IsAtLeast', other)
    if self._actual < other:
      self._FailComparingValues('is at least', other)

  def IsAtMost(self, other):
    self._CheckNone('IsAtMost', other)
    if self._actual > other:
      self._FailComparingValues('is at most', other)

  def IsGreaterThan(self, other):
    self._CheckNone('IsGreaterThan', other)
    if self._actual <= other:
      self._FailComparingValues('is greater than', other)

  def IsLessThan(self, other):
    self._CheckNone('IsLessThan', other)
    if self._actual >= other:
      self._FailComparingValues('is less than', other)

  def _CheckNone(self, proposition, other):
    if other is None and not _PYTHON2:
      raise InvalidAssertionError(
          'It is illegal to compare using {0}({1})'.format(proposition, None))


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

  def HasSize(self, size):
    if len(self._actual) != size:
      self._FailWithBadResults('has a size of', size, 'is', len(self._actual))

  def IsEmpty(self):
    if self._actual:
      self._FailWithProposition('is empty')

  def IsNotEmpty(self):
    if not self._actual:
      self._FailWithProposition('is not empty')

  def Contains(self, element):
    if element not in self._actual:
      self._FailWithSubject('should have contained <{0!r}>'.format(element))

  def DoesNotContain(self, element):
    if element in self._actual:
      self._FailWithSubject(
          'should not have contained <{0!r}>'.format(element))

  def ContainsNoDuplicates(self):
    # Dictionaries and Sets have unique members by definition; avoid iterating.
    if isinstance(self._actual, (collections.Mapping, collections.Set)):
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

  def ContainsAllIn(self, expected):
    return self._ContainsAll('contains all elements in', expected)

  def ContainsAllOf(self, *expected):
    return self._ContainsAll('contains all of', expected)

  def ContainsAnyIn(self, expected):
    return self._ContainsAny('contains any element in', expected)

  def ContainsAnyOf(self, *expected):
    return self._ContainsAny('contains any of', expected)

  def ContainsExactly(self, *expected):
    expecting_single_iterable = len(expected) == 1 and _IsIterable(expected)
    return self._ContainsExactlyElementsIn(
        expected, warn_elements_in=expecting_single_iterable)

  def ContainsExactlyElementsIn(self, expected):
    return self._ContainsExactlyElementsIn(expected)

  def ContainsNoneIn(self, excluded):
    self._ContainsNone('contains no elements in', excluded)

  def ContainsNoneOf(self, *excluded):
    self._ContainsNone('contains none of', excluded)

  def IsOrdered(self):
    self.IsOrderedAccordingTo(Cmp)

  def IsOrderedAccordingTo(self, comparator):
    self._PairwiseCheck(lambda a, b: comparator(a, b) <= 0, strict=False)

  def IsStrictlyOrdered(self):
    self.IsStrictlyOrderedAccordingTo(Cmp)

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
    missing = collections.OrderedDict()
    actual_not_in_order = set()
    ordered = True

    # Step through the expected elements.
    for i in expected:
      try:
        index = actual_list.index(i)
        # Drain all the elements before that element into actual_not_in_order.
        for _ in Range(index):
          actual_not_in_order.add(actual_list.pop(0))
        # And remove the element from the actual_list.
        actual_list.pop(0)
      except ValueError:
        try:
          actual_not_in_order.remove(i)
          # If it was in actual_not_in_order, we're not in order.
          ordered = False
        except KeyError:
          # It is not in actual_not_in_order, we're missing an expected element.
          missing.setdefault(i, 0)
          missing[i] += 1

    # If we have any missing expected elements, fail.
    if missing:
      self._FailWithBadResults(
          verb, expected, 'is missing', self._CountDuplicates(missing))

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
      True if the subject contains any of the expected elements.

    Raises:
      TruthAssertionError: the subject is missing all of the expected elements.
    """
    for i in expected:
      if i in self._actual:
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

    missing = collections.OrderedDict()
    extra = collections.OrderedDict()
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
        extra[actual_element] = 1
        break

      # As soon as we encounter a pair of elements that differ, we know that
      # InOrder() cannot succeed, so we can check the rest of the elements
      # more normally. Since any previous pairs of elements we iterated
      # over were equal, they have no effect on the result now.
      if actual_element != expected_element:
        # Missing elements; elements that are not missing will be removed.
        missing[expected_element] = 1
        for m in expected_iter:
          missing.setdefault(m, 0)
          missing[m] += 1

        # Remove all actual elements from missing, and add any that weren't
        # in missing to extra.
        if actual_element in missing:
          missing[actual_element] -= 1
          if not missing[actual_element]:
            del missing[actual_element]
        else:
          extra[actual_element] = 1
        for e in actual_iter:
          if e in missing:
            missing[e] -= 1
            if not missing[e]:
              del missing[e]
          else:
            extra.setdefault(e, 0)
            extra[e] += 1

        # Fail if there are either missing or extra elements.

        if missing:
          if extra:
            # Subject is missing required elements and has extra elements.
            self._FailWithProposition(
                'contains exactly <{0!r}>.'
                ' It is missing <{1}> and has unexpected items <{2}>'
                .format(
                    expected,
                    self._CountDuplicates(missing),
                    self._CountDuplicates(extra)),
                suffix=warning)
          else:
            self._FailWithBadResults(
                'contains exactly', expected,
                'is missing', self._CountDuplicates(missing),
                suffix=warning)
        if extra:
          self._FailWithBadResults(
              'contains exactly', expected,
              'has unexpected items', self._CountDuplicates(extra),
              suffix=warning)

        # The iterables were not in the same order, InOrder() can just fail.
        return _NotInOrder(
            self._actual, 'contains exactly these elements in order', expected)

    # We must have reached the end of one of the iterators without finding any
    # pairs of elements that differ. If the actual iterator still has elements,
    # they're extras. If the required iterator has elements, they're missing.
    for e in actual_iter:
      extra.setdefault(e, 0)
      extra[e] += 1
    if extra:
      self._FailWithBadResults(
          'contains exactly', expected,
          'has unexpected items', self._CountDuplicates(extra),
          suffix=warning)

    for m in expected_iter:
      missing.setdefault(m, 0)
      missing[m] += 1
    if missing:
      self._FailWithBadResults(
          'contains exactly', expected,
          'is missing', self._CountDuplicates(missing),
          suffix=warning)

    # If neither iterator has elements, we reached the end and the elements
    # were in order, so InOrder() can just succeed.
    return _InOrder()

  def _ContainsNone(self, fail_verb, excluded):
    present = []
    for i in excluded:
      if i in self._actual:
        present.append(i)
    if present:
      self._FailWithBadResults(fail_verb, excluded, 'contains', present)

  def _CountDuplicates(self, missing):
    missed_list = []
    for item, count in ItemsOf(missing):
      if count == 1:
        missed_list.append('{0!r}'.format(item))
      else:
        missed_list.append('{0!r} [{1} copies]'.format(item, count))
    return '[{0}]'.format(', '.join(missed_list))

  def _PairwiseCheck(self, pair_comparator, strict=False):
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

  def InOrder(self):
    pass


class _NotInOrder(_Ordered):
  """Adverb for an iterable that is already known to be out of order."""

  def __init__(self, actual, check, expected):
    super(_NotInOrder, self).__init__()
    self._actual = actual
    self._check = check
    self._expected = expected

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

  def ContainsKey(self, key):
    if key not in self._actual:
      self._FailWithProposition('contains key <{0}>'.format(key))

  def DoesNotContainKey(self, key):
    if key in self._actual:
      self._FailWithProposition('does not contain key <{0}>'.format(key))

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
    for k, v in ItemsOf(self._actual):
      if v == value:
        other_keys.append(k)
    if other_keys:
      self._FailWithProposition(
          'contains item <{0!r}>.'
          ' However, the following keys are mapped to <{1!r}>: {2!r}'
          .format((key, value), value, other_keys))

    self._FailWithProposition('contains item <{0!r}>'.format((key, value)))

  def DoesNotContainItem(self, key, value):
    if key in self._actual and self._actual[key] == value:
      self._FailWithProposition(
          'does not contain item <{0!r}>'.format((key, value)))

  def ContainsExactly(self, *items):
    if len(items) % 2:
      raise ValueError(
          'There must be an equal number of key/value pairs'
          ' (i.e., the number of key/value parameters ({0}) must be even).'
          .format(len(items)))
    expected = collections.OrderedDict()
    for i in Range(0, len(items), 2):
      expected[items[i]] = items[i + 1]
    return self.ContainsExactlyItemsIn(expected)

  def ContainsExactlyItemsIn(self, expected):
    return AssertThat(self._actual.items()).ContainsExactly(*expected.items())

  # Method aliases when translating Java's Map.Entry to Python's items.
  ContainsEntry = ContainsItem
  DoesNotContainEntry = DoesNotContainItem
  ContainsExactlyEntriesIn = ContainsExactlyItemsIn


class _NumericSubject(_ComparableSubject):
  """Subject for all types of numbers--int, long, float, and complex."""

  def IsZero(self):
    if self._actual != 0:
      self._FailWithProposition('is zero')

  def IsNonZero(self):
    if self._actual == 0:
      self._FailWithProposition('is non-zero')

  def IsFinite(self):
    if math.isinf(self._actual) or math.isnan(self._actual):
      self._FailWithSubject('should have been finite')

  def IsPositiveInfinity(self):
    self.IsEqualTo(POSITIVE_INFINITY)

  def IsNegativeInfinity(self):
    self.IsEqualTo(NEGATIVE_INFINITY)

  def IsNan(self):
    if not math.isnan(self._actual):
      self._FailComparingValues('is equal to', NAN)

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

  def HasLength(self, expected):
    actual_length = len(self._actual)
    if actual_length != expected:
      self._FailWithProposition(
          'has a length of {0}. It is {1}'.format(expected, actual_length))

  def StartsWith(self, prefix):
    if not self._actual.startswith(prefix):
      self._FailComparingValues('starts with', prefix)

  def EndsWith(self, suffix):
    if not self._actual.endswith(suffix):
      self._FailComparingValues('ends with', suffix)

  def Matches(self, regex):
    r = re.compile(regex)
    if not r.match(self._actual):
      self._FailWithProposition('matches <{0}>'.format(r.pattern))

  def DoesNotMatch(self, regex):
    r = re.compile(regex)
    if r.match(self._actual):
      self._FailWithProposition('fails to match <{0}>'.format(r.pattern))

  def ContainsMatch(self, regex):
    r = re.compile(regex)
    if not r.search(self._actual):
      self._FailWithSubject(
          'should have contained a match for <{0}>'.format(r.pattern))

  def DoesNotContainMatch(self, regex):
    r = re.compile(regex)
    if r.search(self._actual):
      self._FailWithSubject(
          'should not have contained a match for <{0}>'.format(r.pattern))


class _MockAssertionConverter(_DefaultSubject):
  """Traps and converts assertions from a mock function to TruthAssertionError.

  This coerces all exceptions thrown by this module to the same type.

  Example usage:
    with self._WrapMockAssertions():
      mock_func.assert_called()
  """

  @contextlib.contextmanager
  def _WrapMockAssertions(self):
    try:
      yield
    except AssertionError as e:
      raise TruthAssertionError(e)


class _MockSubject(_MockAssertionConverter):
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
      AssertThat(mock_func).WasCalled().Once().With(*a, **k)  --OR--
      AssertThat(mock_func).WasCalled().With(*a, **k).Once()

    mock_func.assert_has_calls(calls, any_order=any_order) ->
      AssertThat(mock_func).HasCalls(calls, any_order=any_order)

    mock_func.assert_any_call(*a, **k) ->
      AssertThat(mock_func).WasCalled().With(*a, **k)

  Note that the WasCalled().Once().With(...) and WasCalled().With(...).Once()
  assertions are equivalent, and they assert that the function was called one
  time ever, and that one time it was called, it was passed those arguments.
  The mock library is incapable of asserting a different English interpretation
  wherein the function was passed those arguments exactly once, but is permitted
  to have been called with other, irrelevant arguments.

  Mock subjects can also be used to make value assertions. For example:

    AssertThat(actual_mock).IsAnyOf(mock1, mock2)
    AssertThat(actual_mock).IsEqualTo(expected_mock)
    AssertThat(actual_mock).IsSameAs(expected_mock)
  """

  def WasCalled(self):
    with self._WrapMockAssertions():
      self._actual.assert_called()
    return _MockCalledSubject(self._actual)

  def WasNotCalled(self):
    with self._WrapMockAssertions():
      self._actual.assert_not_called()

  def HasCalls(self, calls, any_order=False):
    with self._WrapMockAssertions():
      self._actual.assert_has_calls(calls, any_order=any_order)


class _MockCalledSubject(_MockAssertionConverter):
  """Subject for a mock already asserted [not] to have been called."""

  def __init__(self, actual):
    super(_MockCalledSubject, self).__init__(actual)
    self._Resolve()

  def Once(self):
    with self._WrapMockAssertions():
      self._actual.assert_called_once()
    return self

  def With(self, *args, **kwargs):
    with self._WrapMockAssertions():
      self._actual.assert_any_call(*args, **kwargs)
    return self

  def LastWith(self, *args, **kwargs):
    with self._WrapMockAssertions():
      self._actual.assert_called_with(*args, **kwargs)


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

  def __getattribute__(self, name):
    if (name.startswith('_') or
        name[0] == name[0].lower() or
        hasattr(_BooleanSubject, name) or
        (_PYTHON2 and
         hasattr(_NumericSubject, name) and
         name not in ('IsWithin', 'IsNotWithin'))):
      return object.__getattribute__(self, name)

    self._Fail(
        'Invalid operation on None subject: <{0}>.'
        ' Check that the actual value of the subject is not None,'
        ' or AssertThat the subject IsNone()/IsNotNone()'.format(name))


# Tight bindings of object superclasses to subject constructors.
# No key in this dictionary should be a subclass of any other key.
# This dictionary must come last because its values are classes defined above.
_TYPE_CONSTRUCTORS = {
    BaseException: _ExceptionSubject,
    BaseString: _StringSubject,
    mock.NonCallableMock: _MockSubject,
    bool: _BooleanSubject,
    collections.Mapping: _DictionarySubject,
    mock.NonCallableMock: _MockSubject,
    NoneType: _NoneSubject
}
if _PYTHON2:
  # In Python 3, types.ClassType simply becomes "type".
  _TYPE_CONSTRUCTORS[types.ClassType] = _ClassSubject


atexit.register(_EmptySubject._CheckUnresolved)
