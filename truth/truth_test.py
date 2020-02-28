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

"""Tests truth module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import collections
import contextlib
import inspect
import io
import os
import re
import sys
import time
import traceback

os.environ.setdefault('PBR_VERSION', '5.1.3')

from absl.testing import absltest
import six
from six.moves import range
import truth

try:
  from unittest import mock
except ImportError:
  from mock import mock

try:
  import collections.abc as collections_abc
except ImportError:
  import collections as collections_abc  # pylint: disable=reimported


TYPE_WORD = 'type' if six.PY2 else 'class'


def Buffer(s):
  # pylint: disable=undefined-variable
  return buffer(s) if six.PY2 else memoryview(bytearray(s, 'ascii'))
  # pylint: enable=undefined-variable


def Long(i):
  return long(i) if six.PY2 else i  # pylint: disable=undefined-variable


class TestClass(object):
  """Test class."""

  test_attribute = True

  def TestMethod(self):
    pass


class TestChildClass(TestClass):
  """Test child class."""


class TestComparableClass(object):
  """Test class that implements the Comparable interface, only."""

  def __lt__(self, other):
    pass

  def __le__(self, other):
    pass

  def __gt__(self, other):
    pass

  def __ge__(self, other):
    pass


class TestMappingClass(collections_abc.Mapping):
  """Test class that implements the Mapping interface."""

  def __getitem__(self, key):
    return True

  def __iter__(self):
    yield True

  def __len__(self):
    return 42


class ClassicTestClass:      # pylint: disable=old-style-class
  """Old-style test class, not inheriting from object."""


class DeclassifiedTestClass(object):
  """Test class that simulates a mock function created by mox.CreateMock()."""

  @property
  def __class__(self):
    return lambda: None


class DeclassifiedListTestClass(list, DeclassifiedTestClass):
  """Test class that simulates a mock.call object."""


class DeclassifiedDictTestClass(dict, DeclassifiedTestClass):
  """Test class that simulates a dictionary object object without a class."""


class BaseTest(absltest.TestCase):
  """Helper class that makes testing failures easier.

  Instead of
    with self.assertRaises(Exception) as e:
      TestExpectedFailure()
      self.assertIn('expected string', e)

  You can write
    with self.Failure('expected string'):
      TestExpectedFailure()
  """

  @contextlib.contextmanager
  def Failure(self, *expected):
    try:
      yield
    except truth.TruthAssertionError as e:
      for s in expected:
        self.assertIn(s, e.args[0])
    else:
      self.fail('expected TruthAssertionError not raised')

  # pylint: disable=invalid-name
  AssertRaisesRegex = getattr(
      absltest.TestCase, 'assertRaisesRegex',
      absltest.TestCase.assertRaisesRegexp)
  # pylint: enable=invalid-name


class AssertThatTest(BaseTest):

  def testStringSubject(self):
    self.AssertSubject('', truth._StringSubject)
    self.AssertSubject(u'', truth._StringSubject)

  def testExceptionSubject(self):
    self.AssertSubject(Exception(), truth._ExceptionSubject)
    self.AssertSubject(OSError(), truth._ExceptionSubject)
    self.AssertSubject(StopIteration(), truth._ExceptionSubject)
    self.AssertSubject(SystemExit(), truth._ExceptionSubject)
    self.AssertSubject(ValueError(), truth._ExceptionSubject)

  def testBooleanSubject(self):
    self.AssertSubject(True, truth._BooleanSubject)
    self.AssertSubject(False, truth._BooleanSubject)

  def testClassSubject(self):
    self.AssertSubject(ClassicTestClass, truth._ClassSubject)
    self.AssertSubject(TestClass, truth._ClassSubject)
    self.AssertSubject(TestChildClass, truth._ClassSubject)

  def testExceptionClassSubject(self):
    self.AssertSubject(Exception, truth._ExceptionClassSubject)
    self.AssertSubject(OSError, truth._ExceptionClassSubject)
    self.AssertSubject(StopIteration, truth._ExceptionClassSubject)
    self.AssertSubject(SystemExit, truth._ExceptionClassSubject)
    self.AssertSubject(ValueError, truth._ExceptionClassSubject)

  def testDictionarySubject(self):
    self.AssertSubject({}, truth._DictionarySubject)
    self.AssertSubject(collections.defaultdict(int), truth._DictionarySubject)
    self.AssertSubject(collections.OrderedDict(), truth._DictionarySubject)
    self.AssertSubject(TestMappingClass(), truth._DictionarySubject)

  @mock.patch('os.path.isdir')
  @mock.patch('time.sleep')
  def testMockPatchSubject(self, mock_sleep, mock_isdir):
    self.AssertSubject(mock_isdir, truth._MockSubject)
    self.AssertSubject(mock_sleep, truth._MockSubject)

  @mock.patch.object(os.path, 'isdir')
  @mock.patch.object(time, 'sleep')
  def testMockPatchObjectSubject(self, mock_sleep, mock_isdir):
    self.AssertSubject(mock_isdir, truth._MockSubject)
    self.AssertSubject(mock_sleep, truth._MockSubject)

  @mock.patch.object(os.path, 'isdir', autospec=True)
  @mock.patch.object(time, 'sleep', autospec=True)
  def testMockPatchObjectAutospecSubject(self, mock_sleep, mock_isdir):
    self.AssertSubject(mock_isdir, truth._MockSubject)
    self.AssertSubject(mock_sleep, truth._MockSubject)

  def testNoneSubject(self):
    self.AssertSubject(None, truth._NoneSubject)

  def testComparableIterableSubject(self):
    self.AssertSubject((), truth._ComparableIterableSubject)
    self.AssertSubject([], truth._ComparableIterableSubject)
    self.AssertSubject(set(), truth._ComparableIterableSubject)
    self.AssertSubject(frozenset(), truth._ComparableIterableSubject)
    self.AssertSubject(bytearray(), truth._ComparableIterableSubject)
    range5 = list(range(5)) if six.PY2 else range(5)
    self.AssertSubject(range5, truth._ComparableIterableSubject)
    self.AssertSubject(collections.deque(), truth._ComparableIterableSubject)

  def testComparableSubject(self):
    self.AssertSubject(TestComparableClass(), truth._ComparableSubject)

  def testNumericSubject(self):
    self.AssertSubject(-5, truth._NumericSubject)
    self.AssertSubject(0, truth._NumericSubject)
    self.AssertSubject(1, truth._NumericSubject)
    self.AssertSubject(5, truth._NumericSubject)
    self.AssertSubject(Long(5), truth._NumericSubject)
    self.AssertSubject(5.5, truth._NumericSubject)
    self.AssertSubject(complex(3, 4), truth._NumericSubject)
    self.AssertSubject(truth.POSITIVE_INFINITY, truth._NumericSubject)
    self.AssertSubject(truth.NEGATIVE_INFINITY, truth._NumericSubject)
    self.AssertSubject(truth.NAN, truth._NumericSubject)

  def testIterableSubject(self):
    self.AssertSubject(iter('abc'), truth._IterableSubject)
    self.AssertSubject(iter(()), truth._IterableSubject)
    self.AssertSubject(iter([]), truth._IterableSubject)
    self.AssertSubject(iter(set()), truth._IterableSubject)
    self.AssertSubject(Buffer(''), truth._IterableSubject)
    self.AssertSubject(io.StringIO(u'buffer'), truth._IterableSubject)
    self.AssertSubject(reversed([1, 2]), truth._IterableSubject)
    self.AssertSubject(sorted([1, 2]), truth._IterableSubject)
    self.AssertSubject(six.moves.xrange(10), truth._IterableSubject)

  def testDefaultSubject(self):
    self.AssertSubject(lambda: None, truth._DefaultSubject)
    self.AssertSubject(self, truth._DefaultSubject)
    self.AssertSubject(mock, truth._DefaultSubject)
    self.AssertSubject(TestClass.TestMethod, truth._DefaultSubject)

  def testDeclassifiedClassSubject(self):
    self.AssertSubject(DeclassifiedTestClass(), truth._DefaultSubject)

  def testNoUnresolvedSubjects(self):
    truth._EmptySubject._CheckUnresolved()

  def testUnresolvedSubjects(self):
    # Do not insert anything between the next two lines:
    expected_line = inspect.currentframe().f_lineno + 1
    subject = truth.AssertThat('thing')
    # because we depend on the line number of the "truth.AssertThat()" call.

    regex = re.compile(
        r'module truth_test.+line {0}.+in testUnresolvedSubjects.+'
        r'truth\.AssertThat\(\'thing\'\)'.format(expected_line),
        re.S)
    with self.AssertRaisesRegex(truth.UnresolvedAssertionError, regex):
      truth._EmptySubject._CheckUnresolved()
    subject._Resolve()

  def AssertSubject(self, target, expected):
    subject = truth.AssertThat(target)
    self.assertIsInstance(subject, expected)
    subject._Resolve()


class IsComparableTest(absltest.TestCase):

  def testIsComparable(self):
    self.assertTrue(truth._IsComparable(()))
    self.assertTrue(truth._IsComparable([]))
    self.assertTrue(truth._IsComparable({}))
    self.assertTrue(truth._IsComparable(set()))
    self.assertTrue(truth._IsComparable(collections.defaultdict(int)))
    self.assertTrue(truth._IsComparable(collections.deque()))
    self.assertTrue(truth._IsComparable(collections.OrderedDict()))
    self.assertTrue(truth._IsComparable(bytearray()))
    self.assertTrue(truth._IsComparable(''))
    self.assertTrue(truth._IsComparable(u''))
    self.assertTrue(truth._IsComparable(1))
    self.assertTrue(truth._IsComparable(Long(1)))
    self.assertTrue(truth._IsComparable(1.0))
    self.assertTrue(truth._IsComparable(complex(0, 1)))
    self.assertTrue(truth._IsComparable(TestClass))
    self.assertTrue(truth._IsComparable(True))

  def testNotComparable(self):
    if six.PY2:
      self.assertFalse(truth._IsComparable(Buffer('')))

  @mock.patch('time.time')
  def testMockedFunction(self, mock_time):
    self.assertTrue(truth._IsComparable(mock_time))


class IsHashableTest(absltest.TestCase):

  def testIsHashable(self):
    self.assertTrue(truth._IsHashable(()))
    self.assertTrue(truth._IsHashable(frozenset()))
    self.assertTrue(truth._IsHashable(''))
    self.assertTrue(truth._IsHashable(u''))
    self.assertTrue(truth._IsHashable(None))
    self.assertTrue(truth._IsHashable(1))
    self.assertTrue(truth._IsHashable(Long(1)))
    self.assertTrue(truth._IsHashable(1.0))
    self.assertTrue(truth._IsHashable(complex(0, 1)))
    self.assertTrue(truth._IsHashable(TestClass))
    self.assertTrue(truth._IsHashable(TestClass()))
    self.assertTrue(truth._IsHashable(True))

  def testIsNotHashable(self):
    self.assertFalse(truth._IsHashable([]))
    self.assertFalse(truth._IsHashable({}))
    self.assertFalse(truth._IsHashable(set()))
    self.assertFalse(truth._IsHashable(collections.defaultdict(int)))
    self.assertFalse(truth._IsHashable(collections.deque()))
    self.assertFalse(truth._IsHashable(collections.OrderedDict()))
    self.assertFalse(truth._IsHashable(bytearray()))
    self.assertFalse(truth._IsHashable(mock.call()))

  def testBuffer(self):
    if six.PY2:
      self.assertTrue(truth._IsHashable(Buffer('')))
    else:
      self.assertFalse(truth._IsHashable(Buffer('')))

  @mock.patch('time.time')
  def testMockedFunction(self, mock_time):
    self.assertTrue(truth._IsHashable(mock_time))


class IsIterableTest(absltest.TestCase):

  def testIsIterable(self):
    self.assertTrue(truth._IsIterable(()))
    self.assertTrue(truth._IsIterable([]))
    self.assertTrue(truth._IsIterable({}))
    self.assertTrue(truth._IsIterable(set()))
    self.assertTrue(truth._IsIterable(collections.defaultdict(int)))
    self.assertTrue(truth._IsIterable(collections.deque()))
    self.assertTrue(truth._IsIterable(collections.OrderedDict()))
    self.assertTrue(truth._IsIterable(bytearray()))
    self.assertTrue(truth._IsIterable(Buffer('')))
    self.assertTrue(truth._IsIterable(''))
    self.assertTrue(truth._IsIterable(u''))

  def testNotIterable(self):
    self.assertFalse(truth._IsIterable(None))
    self.assertFalse(truth._IsIterable(1))
    self.assertFalse(truth._IsIterable(Long(1)))
    self.assertFalse(truth._IsIterable(1.0))
    self.assertFalse(truth._IsIterable(complex(0, 1)))
    self.assertFalse(truth._IsIterable(TestClass))
    self.assertFalse(truth._IsIterable(True))

  @mock.patch('time.time')
  def testMockedFunction(self, mock_time):
    self.assertTrue(truth._IsIterable(mock_time))


class IsMockTest(absltest.TestCase):

  @mock.patch.object(os.path, 'isdir')
  @mock.patch.object(time, 'sleep', autospec=True)
  def testIsMock(self, mock_sleep, mock_isdir):
    self.assertTrue(truth._IsMock(mock_isdir))
    self.assertTrue(truth._IsMock(mock_sleep))

  def testIsNotMock(self):
    self.assertFalse(truth._IsMock(lambda: None))
    self.assertFalse(truth._IsMock(os.path.isdir))
    self.assertFalse(truth._IsMock(time.sleep))
    self.assertFalse(truth._IsMock(None))
    self.assertFalse(truth._IsMock(1))
    self.assertFalse(truth._IsMock(TestClass))
    self.assertFalse(truth._IsMock(TestClass()))
    self.assertFalse(truth._IsMock(DeclassifiedTestClass()))


class IsNumericTest(absltest.TestCase):

  def testIsNumeric(self):
    self.assertTrue(truth._IsNumeric(1))
    self.assertTrue(truth._IsNumeric(Long(1)))
    self.assertTrue(truth._IsNumeric(1.0))
    self.assertTrue(truth._IsNumeric(complex(0, 1)))
    self.assertTrue(truth._IsNumeric(True))       # Booleans subclass ints.
    self.assertTrue(truth._IsNumeric(truth.POSITIVE_INFINITY))
    self.assertTrue(truth._IsNumeric(truth.NEGATIVE_INFINITY))
    self.assertTrue(truth._IsNumeric(truth.NAN))

  def testNotNumeric(self):
    self.assertFalse(truth._IsNumeric(()))
    self.assertFalse(truth._IsNumeric([]))
    self.assertFalse(truth._IsNumeric({}))
    self.assertFalse(truth._IsNumeric(set()))
    self.assertFalse(truth._IsNumeric(collections.defaultdict(int)))
    self.assertFalse(truth._IsNumeric(collections.deque()))
    self.assertFalse(truth._IsNumeric(collections.OrderedDict()))
    self.assertFalse(truth._IsNumeric(bytearray()))
    self.assertFalse(truth._IsNumeric(Buffer('')))
    self.assertFalse(truth._IsNumeric(''))
    self.assertFalse(truth._IsNumeric(u''))
    self.assertFalse(truth._IsNumeric(None))
    self.assertFalse(truth._IsNumeric(TestClass))

  @mock.patch('time.time')
  def testMockedFunction(self, mock_time):
    self.assertFalse(truth._IsNumeric(mock_time))


class DescribeTimesTest(absltest.TestCase):

  def testOnce(self):
    self.assertEqual(truth._DescribeTimes(1), 'once')
    self.assertEqual(truth._DescribeTimes(1.0), 'once')

  def testAnythingButOne(self):
    self.assertEqual(truth._DescribeTimes(-1), '-1 times')
    self.assertEqual(truth._DescribeTimes(0), '0 times')
    self.assertEqual(truth._DescribeTimes(2), '2 times')
    self.assertEqual(truth._DescribeTimes(263), '263 times')
    self.assertEqual(truth._DescribeTimes(29.35), '29.35 times')


class AssertsTruthTest(absltest.TestCase):

  def testAppliedToProtectedMethod(self):
    with self.assertRaises(AttributeError):
      @truth.asserts_truth
      def _ProtectedMethod():  # pylint: disable=unused-variable
        pass

  def testAssertsTruth(self):
    @truth.asserts_truth
    def RaiseTruthAssertionError():
      raise truth.TruthAssertionError('test')

    try:
      RaiseTruthAssertionError()
    except truth.TruthAssertionError as e:
      tb = traceback.extract_tb(sys.exc_info()[2])
      if hasattr(e, 'with_traceback'):
        # The two tracebacks are truth.asserts_truth() and this function.
        # The RaisesTruthAssertionError() call is skipped.
        self.assertLen(tb, 2)
      else:
        # If the traceback is immutable, RaiseTruthAssertionError() is included.
        self.assertLen(tb, 3)
    finally:
      del tb  # Prevent circular reference.


class AllowUnresolvedSubjects(absltest.TestCase):
  """Children of this test class may create unresolved subjects.

  Any unresolved subjects are forcibly resolved at the end of each test case.
  Use this mix-in class judiciously, as it may mask real errors.
  """

  def tearDown(self):
    super(AllowUnresolvedSubjects, self).tearDown()
    truth._EmptySubject._ResolveAll()


class EmptySubjectTest(BaseTest, AllowUnresolvedSubjects):

  def testGetSubject(self):
    s = truth._EmptySubject(True)
    self.assertEqual(s._GetSubject(), '<True>')

  def testGetNamedSubject(self):
    s = truth._EmptySubject(True).Named('thing')
    self.assertEqual(s._GetSubject(), 'thing(<True>)')

  def testGetNamedSubjectNameProperty(self):
    s = truth._EmptySubject(True).Named('thing')
    self.assertEqual(s.name, 'thing')

  def testFailComparingValues(self):
    s = truth._EmptySubject(5)
    with self.Failure('Not true that <5> is equal to <3>.'):
      s._FailComparingValues('is equal to', 3)

  def testFailWithBadResults(self):
    s = truth._EmptySubject([1, 2])
    with self.Failure(
        'Not true that <[1, 2]> has length <1>. It is <2>.'):
      s._FailWithBadResults('has length', 1, 'is', 2)

  def testFailWithBadResultsAndSuffix(self):
    s = truth._EmptySubject([1, 2])
    with self.Failure(
        'Not true that <[1, 2]> has length <1>. It is <2>. Too bad!'):
      s._FailWithBadResults('has length', 1, 'is', 2, suffix=' Too bad!')

  def testFailWithProposition(self):
    s = truth._EmptySubject(5)
    with self.Failure('Not true that <5> is negative.'):
      s._FailWithProposition('is negative')

  def testFailWithPropositionAndSuffix(self):
    s = truth._EmptySubject(5)
    with self.Failure('Not true that <5> is negative. It is positive.'):
      s._FailWithProposition('is negative', suffix=' It is positive.')

  def testFailWithSubject(self):
    s = truth._EmptySubject('thing')
    with self.Failure('failed'):
      s._FailWithSubject('<thing> failed')

  def testFail(self):
    s = truth._EmptySubject(None)
    with self.Failure('message'):
      s._Fail('message')

  @mock.patch.object(os.path, 'exists', side_effect=ValueError('mock called'))
  def testInitWithMockedOsPathExists(self, unused_mock_exists):
    truth._EmptySubject(None)

  def testStrWhenNotCreatedByAssertThat(self):
    s = truth._EmptySubject('subject')
    self.assertEqual(str(s), "_EmptySubject(<'subject'>)")


class DefaultSubjectTest(BaseTest):

  def testIsEqualTo(self):
    s = truth._DefaultSubject(5)
    s.IsEqualTo(5)
    with self.Failure('is equal to <3>'):
      s.IsEqualTo(3)

  def testIsEqualToFailsButFormattedRepresentationsAreEqual(self):
    class StrReprTestClass(object):

      def __init__(self, str_value, repr_value):
        self.str = str_value
        self.repr = repr_value

      def __str__(self):
        return self.str

      def __repr__(self):
        return self.repr

    s = truth._DefaultSubject(StrReprTestClass('s1', 'r1'))
    with self.Failure('their str() representations are equal'):
      s.IsEqualTo(StrReprTestClass('s1', 'r2'))
    with self.Failure('their repr() representations are equal'):
      s.IsEqualTo(StrReprTestClass('s2', 'r1'))

  def testIsNotEqualTo(self):
    s = truth._DefaultSubject(5)
    s.IsNotEqualTo(3)
    with self.Failure('is not equal to <5>'):
      s.IsNotEqualTo(5)

  def testNone(self):
    s = truth._DefaultSubject(None)
    s.IsNone()
    with self.Failure('is not None'):
      s.IsNotNone()

  def testNotNone(self):
    s = truth._DefaultSubject('abc')
    s.IsNotNone()
    with self.Failure('is None'):
      s.IsNone()

  def testIsIn(self):
    s = truth._DefaultSubject(3)
    s.IsIn((3,))
    s.IsIn((3, 5))
    s.IsIn((1, 3, 5))
    s.IsIn({3: 'three'})
    s.IsIn(frozenset((3, 5)))
    with self.Failure('is equal to any of <()>'):
      s.IsIn(())
    with self.Failure('is equal to any of <(2,)>'):
      s.IsIn((2,))

  def testIsNotIn(self):
    s = truth._DefaultSubject(3)
    s.IsNotIn((5,))
    s.IsNotIn(frozenset((5,)))
    s.IsNotIn(('3',))
    with self.Failure('is not in (3,)', 'found at index 0'):
      s.IsNotIn((3,))
    with self.Failure('is not in (1, 3)', 'found at index 1'):
      s.IsNotIn((1, 3))
    with self.Failure('is not in {0!r}'.format(frozenset([3]))):
      s.IsNotIn(frozenset((3,)))

  def testIsAnyOf(self):
    s = truth._DefaultSubject(3)
    s.IsAnyOf(3)
    s.IsAnyOf(3, 5)
    s.IsAnyOf(1, 3, 5)
    with self.Failure('is equal to any of <()>'):
      s.IsAnyOf()
    with self.Failure('is equal to any of <(2,)>'):
      s.IsAnyOf(2)

  def testIsNoneOf(self):
    s = truth._DefaultSubject(3)
    s.IsNoneOf(5)
    s.IsNoneOf('3')
    with self.Failure('is not in (3,)', 'found at index 0'):
      s.IsNoneOf(3)
    with self.Failure('is not in (1, 3)', 'found at index 1'):
      s.IsNoneOf(1, 3)

  def testIsInstanceOf(self):
    s = truth._DefaultSubject(TestChildClass())
    s.IsInstanceOf(TestChildClass)
    s.IsInstanceOf(TestClass)
    s.IsInstanceOf(object)
    with self.Failure("is an instance of <<{0} 'int'>>".format(TYPE_WORD)):
      s.IsInstanceOf(int)
    with self.Failure('is an instance of', 'ClassicTestClass'):
      s.IsInstanceOf(ClassicTestClass)

  def testIsNotInstanceOf(self):
    s = truth._DefaultSubject(TestChildClass())
    s.IsNotInstanceOf(int)
    s.IsNotInstanceOf(ClassicTestClass)
    with self.Failure('expected not to be an instance of', 'TestChildClass'):
      s.IsNotInstanceOf(TestChildClass)
    with self.Failure('expected not to be an instance of', 'TestChildClass'):
      s.IsNotInstanceOf(TestClass)
    with self.Failure('expected not to be an instance of', 'TestChildClass'):
      s.IsNotInstanceOf(object)

  def testIsSameAs(self):
    obj1 = TestClass()
    obj2 = TestClass()
    s = truth._DefaultSubject(obj1)
    s.IsSameAs(obj1)
    with self.Failure('is the same instance as'):
      s.IsSameAs(obj2)

  def testIsNotSameAs(self):
    obj1 = TestClass()
    obj2 = TestClass()
    s = truth._DefaultSubject(obj1)
    s.IsNotSameAs(obj2)
    with self.Failure('is not the same instance as'):
      s.IsNotSameAs(obj1)

  def testTruthyThings(self):
    for t in (1, True, 2, [3], {4: 'four'}, set([5]), -1, 1j, 's', u'u',
              bytearray(1), Buffer('b')):
      truth._DefaultSubject(t).IsTruthy()
      with self.Failure(repr(t), 'is falsy'):
        truth._DefaultSubject(t).IsFalsy()
      with self.Failure(repr(t), 'is False'):
        truth._DefaultSubject(t).IsFalse()
      if t is not True:
        with self.Failure(repr(t), 'is True', 'is truthy'):
          truth._DefaultSubject(t).IsTrue()

  def testFalsyThings(self):
    # https://docs.python.org/2/library/stdtypes.html#truth-value-testing
    for f in (None, False, 0, Long(0), 0.0, 0j, '', u'', (), [], {},
              set(), frozenset(),
              collections.OrderedDict(), collections.defaultdict(),
              bytearray(), Buffer('')):
      truth._DefaultSubject(f).IsFalsy()
      with self.Failure(str(f), 'is truthy'):
        truth._DefaultSubject(f).IsTruthy()
      with self.Failure(repr(f), 'is True'):
        truth._DefaultSubject(f).IsTrue()
      if f is not False:
        with self.Failure(repr(f), 'is False', 'is falsy'):
          truth._DefaultSubject(f).IsFalse()

  def testHasAttribute(self):
    s = truth._DefaultSubject(TestClass())
    s.HasAttribute('test_attribute')
    s.HasAttribute('TestMethod')
    s.HasAttribute('__class__')
    with self.Failure("has attribute <'other_attribute'>"):
      s.HasAttribute('other_attribute')

  def testDoesNotHaveAttribute(self):
    s = truth._DefaultSubject(TestClass())
    s.DoesNotHaveAttribute('other_attribute')
    with self.Failure("does not have attribute <'test_attribute'>"):
      s.DoesNotHaveAttribute('test_attribute')
    with self.Failure("does not have attribute <'TestMethod'>"):
      s.DoesNotHaveAttribute('TestMethod')
    with self.Failure("does not have attribute <'__class__'>"):
      s.DoesNotHaveAttribute('__class__')

  def testIsCallable(self):
    test = lambda t: truth._DefaultSubject(t).IsCallable()
    test(test)
    test(self.testIsCallable)
    test(TestClass().TestMethod)
    with self.Failure('is callable'):
      test(None)
    with self.Failure('is callable'):
      test('abc')

  def testIsNotCallable(self):
    test = lambda t: truth._DefaultSubject(t).IsNotCallable()
    test(None)
    test('abc')
    with self.Failure('is not callable'):
      test(test)
    with self.Failure('is not callable'):
      test(self.testIsNotCallable)
    with self.Failure('is not callable'):
      test(TestClass().TestMethod)


class UnresolvedContextMixinTest(BaseTest):

  def testRaises(self):
    with self.Failure('forget to call IsRaised'):
      with truth._UnresolvedContextMixin():
        pass


class ExceptionSubjectTest(BaseTest):

  def testHasMessage(self):
    s = truth._ExceptionSubject(ValueError('error text'))
    s.HasMessage('error text')
    with self.Failure("is equal to <'error'>"):
      s.HasMessage('error')

  @mock.patch.object(truth, 'AssertThat',
                     return_value=mock.sentinel.FakeAssertThat)
  def testHasMessageThat(self, mock_assert_that):
    s = truth._ExceptionSubject(ValueError('error text'))
    self.assertIs(s.HasMessageThat(), mock.sentinel.FakeAssertThat)
    mock_assert_that.assert_called_once_with('error text')

  @mock.patch.object(truth, 'AssertThat',
                     return_value=mock.sentinel.FakeAssertThat)
  def testHasArgsThat(self, mock_assert_that):
    s = truth._ExceptionSubject(ValueError('error text', 123))
    self.assertIs(s.HasArgsThat(), mock.sentinel.FakeAssertThat)
    mock_assert_that.assert_called_once_with(('error text', 123))

  def testIsRaisedWithMessage(self):
    s = truth._ExceptionSubject(ValueError('error text'))
    with s.IsRaised():
      raise ValueError('error text')

    if six.PY2:
      with self.Failure("is equal to <'error text'>"):
        with s.IsRaised():
          raise ValueError('other text')
    else:
      with self.Failure(
          "missing <['error text']>", "unexpected items <['other text']>"):
        with s.IsRaised():
          raise ValueError('other text')

    if six.PY2:
      with self.Failure("is equal to <'error text'>"):
        with s.IsRaised():
          raise ValueError('error text', 234)
    else:
      with self.Failure('unexpected items <[234]>'):
        with s.IsRaised():
          raise ValueError('error text', 234)

    with self.Failure('should have been raised'):
      with s.IsRaised():
        pass
    with self.Failure('but caught <OSError'):
      with s.IsRaised():
        raise OSError('os error')

  def testIsRaisedWithArgs(self):
    s = truth._ExceptionSubject(ValueError('error text', 123))
    with s.IsRaised():
      raise ValueError('error text', 123)

    if six.PY2:
      with self.Failure("is equal to <''>"):
        with s.IsRaised():
          raise ValueError('other text')
    else:
      with self.Failure(
          "missing <['error text', 123]>", "unexpected items <['other text']>"):
        with s.IsRaised():
          raise ValueError('other text')

    with self.Failure('missing <[123]>', 'unexpected items <[234]>'):
      with s.IsRaised():
        raise ValueError('error text', 234)
    with self.Failure('should have been raised'):
      with s.IsRaised():
        pass
    with self.Failure('but caught <OSError'):
      with s.IsRaised():
        raise OSError('os error')

  def testUnresolvedContext(self):
    s = truth._ExceptionSubject(ValueError('error text', 123))
    with self.Failure('forget to call IsRaised'):
      with s:
        pass

  @mock.patch.object(six, 'PY2', new=False)
  def testPython3GetActualMessageFromEmptyError(self):
    e = truth._ExceptionSubject(ValueError())
    self.assertEqual(e._GetActualMessage(), '')

  @mock.patch.object(six, 'PY2', new=False)
  def testPython3GetActualMessageFromArgs(self):
    e = truth._ExceptionSubject(ValueError('arg1'))
    self.assertEqual(e._GetActualMessage(), 'arg1')


class BooleanSubjectTest(BaseTest):

  def testTrue(self):
    s = truth._BooleanSubject(True)
    s.IsTrue()
    with self.Failure('expected to be False, but was True'):
      s.IsFalse()

  def testFalse(self):
    s = truth._BooleanSubject(False)
    s.IsFalse()
    with self.Failure('expected to be True, but was False'):
      s.IsTrue()


class ClassSubjectTest(BaseTest):

  def testIsSubclassOfSelf(self):
    s = truth._ClassSubject(TestClass)
    s.IsSubclassOf(TestClass)

  def testIsSubclassOfObject(self):
    s = truth._ClassSubject(TestClass)
    s.IsSubclassOf(object)

  def testIsSubclassOfParent(self):
    s = truth._ClassSubject(TestChildClass)
    s.IsSubclassOf(TestClass)

  def testIsSubclassOfNot(self):
    s = truth._ClassSubject(TestClass)
    with self.Failure('is a subclass of', 'TestChildClass'):
      s.IsSubclassOf(TestChildClass)


class ExceptionClassSubjectTest(BaseTest):

  def testIsRaised(self):
    s = truth._ExceptionClassSubject(ValueError)
    with s.IsRaised():
      raise ValueError()

  def testIsNotRaised(self):
    s = truth._ExceptionClassSubject(ValueError)
    with self.Failure('should have been raised'):
      with s.IsRaised():
        pass

  def testDifferentType(self):
    s = truth._ExceptionClassSubject(ValueError)
    with self.Failure('but caught <OSError'):
      with s.IsRaised():
        raise OSError('os error')

  def testIsRaisedMatching(self):
    s = truth._ExceptionClassSubject(ValueError)
    with s.IsRaised(matching=r'bcd'):
      raise ValueError('abcdefg')
    with s.IsRaised(matching=r'b.d'):
      raise ValueError('abcdefg')
    with s.IsRaised(matching=re.compile(r'b.d')):
      raise ValueError('abcdefg')
    with self.Failure('should have contained a match for <b(c)d>'):
      with s.IsRaised(matching=r'b(c)d'):
        raise ValueError('ab(c)d')
    with self.Failure('should have contained a match for <abc>'):
      with s.IsRaised(matching=r'abc'):
        raise ValueError('def')

  def testIsRaisedContaining(self):
    s = truth._ExceptionClassSubject(ValueError)
    with s.IsRaised(containing='bcd'):
      raise ValueError('abcdefg')
    with s.IsRaised(containing='b(c)d'):
      raise ValueError('ab(c)defg')
    with self.Failure("should have contained <'abc'>"):
      with s.IsRaised(containing='abc'):
        raise ValueError('def')
    with self.Failure("should have contained <'b.d'>"):
      with s.IsRaised(containing='b.d'):
        raise ValueError('abcdefg')

  def testIsRaisedMatchingAndContaining(self):
    s = truth._ExceptionClassSubject(ValueError)
    with s.IsRaised(matching=r'b', containing='c'):
      raise ValueError('abcdefg')
    with s.IsRaised(matching=r'b.d', containing='fg'):
      raise ValueError('abcdefg')
    with self.Failure('should have contained a match for <abc>'):
      with s.IsRaised(matching=r'abc', containing='def'):
        raise ValueError('def')
    with self.Failure("should have contained <'def'>"):
      with s.IsRaised(matching=r'abc', containing='def'):
        raise ValueError('abc')

  def testUnresolvedContext(self):
    s = truth._ExceptionClassSubject(ValueError)
    with self.Failure('forget to call IsRaised'):
      with s:
        pass


class ComparableSubjectTest(BaseTest):

  def testIsAtLeast(self):
    s = truth._ComparableSubject(5)
    s.IsAtLeast(3)
    s.IsAtLeast(5)
    with self.Failure('is at least <8>'):
      s.IsAtLeast(8)

  def testIsAtMost(self):
    s = truth._ComparableSubject(5)
    s.IsAtMost(5)
    s.IsAtMost(8)
    with self.Failure('is at most <3>'):
      s.IsAtMost(3)

  def testIsGreaterThan(self):
    s = truth._ComparableSubject(5)
    s.IsGreaterThan(3)
    with self.Failure('is greater than <5>'):
      s.IsGreaterThan(5)
    with self.Failure('is greater than <8>'):
      s.IsGreaterThan(8)

  def testIsLessThan(self):
    s = truth._ComparableSubject(5)
    s.IsLessThan(8)
    with self.Failure('is less than <5>'):
      s.IsLessThan(5)
    with self.Failure('is less than <3>'):
      s.IsLessThan(3)

  @mock.patch.object(six, 'PY2', new=False)
  def testPython3CannotCompareToNone(self):
    s = truth._ComparableSubject(5)
    with self.Failure('illegal to compare', 'IsAtLeast'):
      s.IsAtLeast(None)
    with self.Failure('illegal to compare', 'IsAtMost'):
      s.IsAtMost(None)
    with self.Failure('illegal to compare', 'IsGreaterThan'):
      s.IsGreaterThan(None)
    with self.Failure('illegal to compare', 'IsLessThan'):
      s.IsLessThan(None)


class DuplicateCounterTest(absltest.TestCase):

  def testContains(self):
    d = truth._DuplicateCounter()      # {}
    self.assertNotIn('a', d)
    self.assertNotIn('b', d)

    d.Increment('a')                   # {'a': 1}
    self.assertIn('a', d)
    self.assertNotIn('b', d)

    d.Decrement('a')                   # {}
    self.assertNotIn('a', d)
    self.assertNotIn('b', d)

  def testLen(self):
    d = truth._DuplicateCounter()
    self.assertEmpty(d)
    d.Increment('a')
    self.assertLen(d, 1)
    d.Increment(['a'])
    self.assertLen(d, 2)

  def testEverything(self):
    # It's much easier to test Increment() and Decrement()'s effects on
    # len() and str() using an integration test like this.
    d = truth._DuplicateCounter()      # {}
    self.assertFalse(d)
    self.assertEmpty(d)
    self.assertEqual(str(d), '[]')

    d.Increment('a')                   # {'a': 1}
    self.assertTrue(d)
    self.assertLen(d, 1)
    self.assertEqual(str(d), "['a']")

    d.Increment('a')                   # {'a': 2}
    self.assertTrue(d)
    self.assertLen(d, 1)
    self.assertEqual(str(d), "['a' [2 copies]]")

    d.Increment('b')                   # {'a': 2, 'b': 1}
    self.assertTrue(d)
    self.assertLen(d, 2)
    self.assertEqual(str(d), "['a' [2 copies], 'b']")

    d.Decrement('a')                   # {'a': 1, 'b': 1}
    self.assertTrue(d)
    self.assertLen(d, 2)
    self.assertEqual(str(d), "['a', 'b']")

    d.Decrement('a')                   # {'b': 1}
    self.assertTrue(d)
    self.assertLen(d, 1)
    self.assertEqual(str(d), "['b']")

    d.Increment('a')                   # {'b': 1, 'a': 1}
    self.assertTrue(d)
    self.assertLen(d, 2)
    self.assertEqual(str(d), "['b', 'a']")

    d.Decrement('a')                   # {'b': 1}
    self.assertTrue(d)
    self.assertLen(d, 1)
    self.assertEqual(str(d), "['b']")

    d.Decrement('b')                   # {}
    self.assertFalse(d)
    self.assertEmpty(d)
    self.assertEqual(str(d), '[]')

    d.Decrement('a')                   # {}
    self.assertFalse(d)
    self.assertEmpty(d)
    self.assertEqual(str(d), '[]')

  def testUnhashableKeys(self):
    d = truth._DuplicateCounter()      # {}
    self.assertNotIn([], d)

    d.Increment(['a'])                 # {['a']: 1}
    self.assertIn(['a'], d)
    self.assertLen(d, 1)
    self.assertEqual(str(d), "[['a']]")

    d.Decrement(['a'])                 # {}
    self.assertNotIn([], d)
    self.assertEmpty(d)
    self.assertEqual(str(d), '[]')

  def testIncrementEquivalentDictionaries(self):
    d = truth._DuplicateCounter()
    d.Increment({'a': ['b', 'c']})     # These dictionaries are all the same.
    d.Increment({u'a': ['b', 'c']})
    d.Increment({'a': [u'b', 'c']})
    d.Increment({'a': ['b', u'c']})
    self.assertLen(d, 1)
    self.assertEqual(str(d), "[{'a': ['b', 'c']} [4 copies]]")

  def testDecrementEquivalentDictionaries(self):
    d = truth._DuplicateCounter()
    d.Increment({'a': ['b', 'c']})     # These dictionaries are all the same.
    d.Increment({u'a': ['b', 'c']})
    self.assertLen(d, 1)
    d.Decrement({'a': [u'b', 'c']})
    self.assertLen(d, 1)
    d.Decrement({'a': ['b', u'c']})
    self.assertEmpty(d)
    d.Decrement({'a': [u'b', u'c']})
    self.assertEmpty(d)


class IterableSubjectTest(BaseTest):

  def testHasSize(self):
    s = truth._IterableSubject((2, 5, 8))
    s.HasSize(3)
    with self.Failure('has a size of <-1>', 'It is <3>'):
      s.HasSize(-1)
    with self.Failure('has a size of <2>', 'It is <3>'):
      s.HasSize(2)

  def testIsEmpty(self):
    for e in ((), [], {}, frozenset(), ''):
      s = truth._IterableSubject(e)
      s.IsEmpty()
    for e in ((3,), [4], {5: 6}, frozenset((7,)), 'eight'):
      s = truth._IterableSubject(e)
      with self.Failure('is empty'):
        s.IsEmpty()

  def testIsNotEmpty(self):
    for e in ((3,), [4], {5: 6}, frozenset((7,)), 'eight'):
      s = truth._IterableSubject(e)
      s.IsNotEmpty()
    for e in ((), [], {}, frozenset(), ''):
      s = truth._IterableSubject(e)
      with self.Failure('is not empty'):
        s.IsNotEmpty()

  def testContains(self):
    s = truth._IterableSubject((2, 5, []))
    s.Contains(2)
    s.Contains(5)
    s.Contains([])
    with self.Failure('should have contained <3>'):
      s.Contains(3)
    with self.Failure("should have contained <'2'>"):
      s.Contains('2')
    with self.Failure('should have contained <{}>'):
      s.Contains({})

  def testDoesNotContain(self):
    s = truth._IterableSubject((2, 5, []))
    s.DoesNotContain(3)
    s.DoesNotContain('2')
    s.DoesNotContain({})
    with self.Failure('should not have contained <2>'):
      s.DoesNotContain(2)
    with self.Failure('should not have contained <5>'):
      s.DoesNotContain(5)
    with self.Failure('should not have contained <[]>'):
      s.DoesNotContain([])

  def testContainsNoDuplicates(self):
    truth._IterableSubject(()).ContainsNoDuplicates()
    truth._IterableSubject('abc').ContainsNoDuplicates()
    truth._IterableSubject((2,)).ContainsNoDuplicates()
    truth._IterableSubject((2, 5)).ContainsNoDuplicates()
    truth._IterableSubject({2: 2}).ContainsNoDuplicates()
    truth._IterableSubject(frozenset((2,))).ContainsNoDuplicates()

    with self.Failure('has the following duplicates', "['a', 'a']"):
      truth._IterableSubject('aaa').ContainsNoDuplicates()
    with self.Failure('has the following duplicates', '[2]'):
      truth._IterableSubject((3, 2, 5, 2)).ContainsNoDuplicates()

  def testContainsAllIn(self):
    s = truth._IterableSubject((3, 5, []))
    self.assertIsInstance(s.ContainsAllIn(()), truth._InOrder)
    self.assertIsInstance(s.ContainsAllIn((3,)), truth._InOrder)
    self.assertIsInstance(s.ContainsAllIn((3, [])), truth._InOrder)
    self.assertIsInstance(s.ContainsAllIn((3, 5, [])), truth._InOrder)
    self.assertIsInstance(s.ContainsAllIn(([], 3, 5)), truth._NotInOrder)
    with self.Failure('contains all elements', 'missing <[2]>'):
      s.ContainsAllIn((2, 3))
    with self.Failure('contains all elements', 'missing <[2, 6]>'):
      s.ContainsAllIn((2, 3, 6))

  def testContainsAllOf(self):
    s = truth._IterableSubject((3, 5, []))
    self.assertIsInstance(s.ContainsAllOf(), truth._InOrder)
    self.assertIsInstance(s.ContainsAllOf(3), truth._InOrder)
    self.assertIsInstance(s.ContainsAllOf(3, []), truth._InOrder)
    self.assertIsInstance(s.ContainsAllOf(3, 5, []), truth._InOrder)
    self.assertIsInstance(s.ContainsAllOf([], 3, 5), truth._NotInOrder)
    with self.Failure('contains all of', 'missing <[2]>'):
      s.ContainsAllOf(2, 3)
    with self.Failure('contains all of', 'missing <[2, 6]>'):
      s.ContainsAllOf(2, 3, 6)

  def testContainsAllMixedHashableElements(self):
    s = truth._IterableSubject((3, [], 5, 8))
    self.assertIsInstance(s.ContainsAllOf(3, [], 5, 8), truth._InOrder)
    self.assertIsInstance(s.ContainsAllOf(5, 3, 8, []), truth._NotInOrder)
    with self.Failure('contains all of', 'missing <[9]>'):
      s.ContainsAllOf(3, [], 8, 5, 9)
    with self.Failure('contains all of', 'missing <[{}]>'):
      s.ContainsAllOf(3, [], 8, 5, {})
    with self.Failure('contains all of', 'missing <[9]>'):
      s.ContainsAllOf(8, 3, [], 9, 5)

  def testContainsAnyIn(self):
    s = truth._IterableSubject((3, 5, []))
    s.ContainsAnyIn((3,))
    s.ContainsAnyIn((7, 3))
    with self.Failure('contains any element in'):
      s.ContainsAnyIn(())
    with self.Failure('contains any element in'):
      s.ContainsAnyIn((2, 6))

  def testContainsAnyOf(self):
    s = truth._IterableSubject((3, 5, []))
    s.ContainsAnyOf(3)
    s.ContainsAnyOf(7, 3)
    with self.Failure('contains any of'):
      s.ContainsAnyOf()
    with self.Failure('contains any of'):
      s.ContainsAnyOf(2, 6)

  def testContainsExactly(self):
    s = truth._IterableSubject((3, 5, []))
    self.assertIsInstance(s.ContainsExactly(3, 5, []), truth._InOrder)
    self.assertIsInstance(s.ContainsExactly([], 3, 5), truth._NotInOrder)
    with self.Failure('contains exactly', 'is missing <[9]>'):
      s.ContainsExactly(3, 5, [], 9)
    with self.Failure('contains exactly', 'is missing <[9, 10]>'):
      s.ContainsExactly(9, 3, 5, [], 10)
    with self.Failure('contains exactly', 'has unexpected items <[[]]>'):
      s.ContainsExactly(3, 5)
    with self.Failure('contains exactly', 'has unexpected items <[5]>'):
      s.ContainsExactly([], 3)
    with self.Failure('contains exactly', 'has unexpected items <[5, []]>'):
      s.ContainsExactly(3)
    with self.Failure('contains exactly', 'is missing <[4 [2 copies]]>'):
      s.ContainsExactly(4, 4)
    with self.Failure(
        'contains exactly',
        'is missing <[9]>', 'has unexpected items <[[]]>'):
      s.ContainsExactly(3, 5, 9)
    with self.Failure(
        'contains exactly',
        'is missing <[(3, 5, [])]>',
        'often not the correct thing to do'):
      s.ContainsExactly((3, 5, []))
    with self.Failure('is empty'):
      s.ContainsExactly()

  def testContainsExactlyDoesNotWarnIfSingleStringNotContained(self):
    s = truth._IterableSubject(())
    with self.assertRaises(truth.TruthAssertionError) as ctx:
      s.ContainsExactly('abc')
    self.assertNotIn('often not the correct thing to do', ctx.exception.args[0])

  def testContainsExactlyEmptyContainer(self):
    s = truth._IterableSubject(())
    s.ContainsExactly()
    with self.Failure('contains exactly', 'is missing <[3]>'):
      s.ContainsExactly(3)

  def testContainsExactlyElementsIn(self):
    s = truth._IterableSubject((3, 5, []))
    self.assertIsInstance(
        s.ContainsExactlyElementsIn((3, 5, [])), truth._InOrder)
    self.assertIsInstance(
        s.ContainsExactlyElementsIn(([], 3, 5)), truth._NotInOrder)
    with self.Failure('contains exactly', 'is missing <[9]>'):
      s.ContainsExactlyElementsIn((3, 5, [], 9))
    with self.Failure('contains exactly', 'is missing <[9, 10]>'):
      s.ContainsExactlyElementsIn((9, 3, 5, [], 10))
    with self.Failure('contains exactly', 'has unexpected items <[[]]>'):
      s.ContainsExactlyElementsIn((3, 5))
    with self.Failure('contains exactly', 'has unexpected items <[5]>'):
      s.ContainsExactlyElementsIn(([], 3))
    with self.Failure('contains exactly', 'has unexpected items <[5, []]>'):
      s.ContainsExactlyElementsIn((3,))
    with self.Failure('contains exactly', 'is missing <[4 [2 copies]]>'):
      s.ContainsExactlyElementsIn((4, 4))
    with self.Failure(
        'contains exactly',
        'is missing <[9]>', 'has unexpected items <[[]]>'):
      s.ContainsExactlyElementsIn((3, 5, 9))
    with self.Failure('is empty'):
      s.ContainsExactlyElementsIn(())

  def testSequenceIsEqualToUsesContainsExactlyElementsInPlusInOrder(self):
    s = truth._IterableSubject((3, 5, []))
    s.IsEqualTo((3, 5, []))
    with self.Failure('contains exactly', 'in order', '<([], 3, 5)>'):
      s.IsEqualTo(([], 3, 5))
    with self.Failure('contains exactly', 'is missing <[9]>'):
      s.IsEqualTo((3, 5, [], 9))
    with self.Failure('contains exactly', 'is missing <[9, 10]>'):
      s.IsEqualTo((9, 3, 5, [], 10))
    with self.Failure('contains exactly', 'has unexpected items <[[]]>'):
      s.IsEqualTo((3, 5))
    with self.Failure('contains exactly', 'has unexpected items <[5]>'):
      s.IsEqualTo(([], 3))
    with self.Failure('contains exactly', 'has unexpected items <[5, []]>'):
      s.IsEqualTo((3,))
    with self.Failure('contains exactly', 'is missing <[4 [2 copies]]>'):
      s.IsEqualTo((4, 4))
    with self.Failure(
        'contains exactly',
        'is missing <[9]>', 'has unexpected items <[[]]>'):
      s.IsEqualTo((3, 5, 9))
    with self.Failure('is empty'):
      s.IsEqualTo(())

  def testSetIsEqualToUsesContainsExactlyElementsIn(self):
    s = truth._IterableSubject({3, 5, 8})
    s.IsEqualTo({3, 5, 8})
    s.IsEqualTo({8, 3, 5})
    with self.Failure('contains exactly', 'is missing <[9]>'):
      s.IsEqualTo({3, 5, 8, 9})
    with self.Failure('contains exactly', 'is missing <[9, 10]>'):
      s.IsEqualTo({9, 3, 5, 8, 10})
    with self.Failure('contains exactly', 'has unexpected items <[8]>'):
      s.IsEqualTo({3, 5})
    with self.Failure('contains exactly', 'has unexpected items <[5]>'):
      s.IsEqualTo({8, 3})
    unexpected = [i for i in {3, 5, 8} if i in {5, 8}]
    with self.Failure('contains exactly',
                      'has unexpected items <{0!r}>'.format(unexpected)):
      s.IsEqualTo({3})
    with self.Failure('contains exactly', 'is missing <[4]>'):
      s.IsEqualTo({4})
    with self.Failure(
        'contains exactly', 'is missing <[9]>', 'has unexpected items <[8]>'):
      s.IsEqualTo({3, 5, 9})
    with self.Failure('is empty'):
      s.IsEqualTo(set())

  def testSequenceIsEqualToComparedWithNonIterables(self):
    s = truth._IterableSubject((3, 5, []))
    with self.Failure('is equal to <3>'):
      s.IsEqualTo(3)
    with self.Failure('is equal to', 'DeclassifiedTestClass'):
      s.IsEqualTo(DeclassifiedTestClass())

  def testSetIsEqualToComparedWithNonIterables(self):
    s = truth._IterableSubject({3, 5, 8})
    with self.Failure('is equal to <3>'):
      s.IsEqualTo(3)
    with self.Failure('is equal to', 'DeclassifiedTestClass'):
      s.IsEqualTo(DeclassifiedTestClass())

  def testIsEqualToComparedWithDeclassifiedIterable(self):
    s = truth._IterableSubject(DeclassifiedListTestClass())
    expected = DeclassifiedListTestClass()
    s.IsEqualTo(expected)
    expected.append(3)

    # Python 3 handles isinstance(DeclassifiedTestClass, C) without raising.
    if truth._IsIterable(expected):
      expected_failure = 'is missing <[3]>'
    else:
      expected_failure = 'is equal to <[3]>'

    with self.Failure(expected_failure):
      s.IsEqualTo(expected)

  def testContainsExactlyElementsInEmptyContainer(self):
    s = truth._IterableSubject(())
    s.ContainsExactlyElementsIn(())
    with self.Failure('contains exactly', 'is missing <[3]>'):
      s.ContainsExactlyElementsIn((3,))

  def testContainsNoneIn(self):
    s = truth._IterableSubject((3, 5, []))
    s.ContainsNoneIn(())
    s.ContainsNoneIn((2,))
    s.ContainsNoneIn((2, 6))
    with self.Failure('contains no elements', 'contains <[5]>'):
      s.ContainsNoneIn((5,))
    with self.Failure('contains no elements', 'contains <[5]>'):
      s.ContainsNoneIn((2, 5))

  def testContainsNoneOf(self):
    s = truth._IterableSubject((3, 5, []))
    s.ContainsNoneOf()
    s.ContainsNoneOf(2)
    s.ContainsNoneOf(2, 6)
    with self.Failure('contains none of', 'contains <[5]>'):
      s.ContainsNoneOf(5)
    with self.Failure('contains none of', 'contains <[5]>'):
      s.ContainsNoneOf(2, 5)

  def testIsOrdered(self):
    truth._IterableSubject(()).IsOrdered()
    truth._IterableSubject((3,)).IsOrdered()
    truth._IterableSubject((3, 5, 8)).IsOrdered()
    truth._IterableSubject((3, 5, 5)).IsOrdered()
    with self.Failure('is ordered <(5, 4)>'):
      truth._IterableSubject((5, 4)).IsOrdered()
    with self.Failure('is ordered <(5, 4)>'):
      truth._IterableSubject((3, 5, 4)).IsOrdered()

  def testIsOrderedAccordingTo(self):
    r = lambda a, b: truth.Cmp(b, a)
    truth._IterableSubject(()).IsOrderedAccordingTo(r)
    truth._IterableSubject((3,)).IsOrderedAccordingTo(r)
    truth._IterableSubject((8, 5, 3)).IsOrderedAccordingTo(r)
    truth._IterableSubject((5, 5, 3)).IsOrderedAccordingTo(r)
    with self.Failure('is ordered <(4, 5)>'):
      truth._IterableSubject((4, 5)).IsOrderedAccordingTo(r)
    with self.Failure('is ordered <(3, 5)>'):
      truth._IterableSubject((3, 5, 4)).IsOrderedAccordingTo(r)

  def testIsStrictlyOrdered(self):
    truth._IterableSubject(()).IsStrictlyOrdered()
    truth._IterableSubject((3,)).IsStrictlyOrdered()
    truth._IterableSubject((3, 5, 8)).IsStrictlyOrdered()
    with self.Failure('is strictly ordered <(5, 4)>'):
      truth._IterableSubject((5, 4)).IsStrictlyOrdered()
    with self.Failure('is strictly ordered <(5, 5)>'):
      truth._IterableSubject((3, 5, 5)).IsStrictlyOrdered()

  def testIsStrictlyOrderedAccordingTo(self):
    r = lambda a, b: truth.Cmp(b, a)
    truth._IterableSubject(()).IsStrictlyOrderedAccordingTo(r)
    truth._IterableSubject((3,)).IsStrictlyOrderedAccordingTo(r)
    truth._IterableSubject((8, 5, 3)).IsStrictlyOrderedAccordingTo(r)
    with self.Failure('is strictly ordered <(4, 5)>'):
      truth._IterableSubject((4, 5)).IsStrictlyOrderedAccordingTo(r)
    with self.Failure('is strictly ordered <(5, 5)>'):
      truth._IterableSubject((5, 5, 3)).IsStrictlyOrderedAccordingTo(r)

  @mock.patch('time.sleep')
  def testCallArgsListElementComparedWithIsEqualTo(self, mock_sleep):
    mock_sleep(5)
    s = truth._IterableSubject(mock_sleep.call_args_list[0])
    s.IsEqualTo(mock.call(5))


class OrderedTest(absltest.TestCase):

  def testInOrderNotImplemented(self):
    ordered = truth._Ordered()
    with self.assertRaises(NotImplementedError):
      ordered.InOrder()


class InOrderTest(absltest.TestCase):

  def testInOrder(self):
    order = truth._InOrder()
    order.InOrder()


class NotInOrder(BaseTest):

  def testNotInOrder(self):
    order = truth._NotInOrder((2, 5), 'contains in order', (5, 2))
    with self.Failure('contains in order <(5, 2)>'):
      order.InOrder()


class DictionarySubjectTest(BaseTest):

  def testContainsKey(self):
    s = truth._DictionarySubject({2: 'two', None: 'None'})
    s.ContainsKey(2)
    s.ContainsKey(None)
    with self.Failure('contains key <3>'):
      s.ContainsKey(3)
    with self.Failure('contains key <two>'):
      s.ContainsKey('two')

  def testDoesNotContainKey(self):
    s = truth._DictionarySubject({2: 'two', None: 'None'})
    s.DoesNotContainKey(3)
    s.DoesNotContainKey('two')
    with self.Failure('does not contain key <2>'):
      s.DoesNotContainKey(2)
    with self.Failure('does not contain key <None>'):
      s.DoesNotContainKey(None)

  def testContainsItem(self):
    s = truth._DictionarySubject(
        collections.OrderedDict(((2, 'two'), (4, 'four'), ('too', 'two'))))
    s.ContainsItem(2, 'two')
    s.ContainsItem(4, 'four')
    s.ContainsItem('too', 'two')
    with self.Failure(
        "contains item <(2, 'to')>", "has a mapping from <2> to <'two'>"):
      s.ContainsItem(2, 'to')
    with self.Failure(
        "contains item <(7, 'two')>",
        "following keys are mapped to <'two'>: [2, 'too']"):
      s.ContainsItem(7, 'two')
    with self.Failure("contains item <(7, 'seven')>"):
      s.ContainsItem(7, 'seven')

  def testDoesNotContainItem(self):
    s = truth._DictionarySubject(
        collections.OrderedDict(((2, 'two'), (4, 'four'), ('too', 'two'))))
    s.DoesNotContainItem(2, 'to')
    s.DoesNotContainItem(7, 'two')
    s.DoesNotContainItem(7, 'seven')
    with self.Failure("does not contain item <(2, 'two')>"):
      s.DoesNotContainItem(2, 'two')
    with self.Failure("does not contain item <(4, 'four')>"):
      s.DoesNotContainItem(4, 'four')

  def testContainsExactly(self):
    s = truth._DictionarySubject(collections.OrderedDict(
        ((2, 'two'), (4, 'four'))))
    self.assertIsInstance(
        s.ContainsExactly(2, 'two', 4, 'four'), truth._InOrder)
    self.assertIsInstance(
        s.ContainsExactly(4, 'four', 2, 'two'), truth._NotInOrder)

    with self.Failure(
        "contains exactly <((2, 'two'),)>",
        "has unexpected items <[(4, 'four')]>",
        'often not the correct thing to do'):
      s.ContainsExactly(2, 'two')

    with self.Failure(
        "contains exactly <((2, 'two'), (4, 'for'))>",
        "missing <[(4, 'for')]>",
        "has unexpected items <[(4, 'four')]>"):
      s.ContainsExactly(2, 'two', 4, 'for')

    with self.Failure(
        "contains exactly <((2, 'two'), (4, 'four'), (5, 'five'))>",
        "missing <[(5, 'five')]>"):
      s.ContainsExactly(2, 'two', 4, 'four', 5, 'five')

  def testContainsExactlyPassingOddNumberOfArgs(self):
    s = truth._DictionarySubject({})
    with self.AssertRaisesRegex(ValueError, r'parameters \(3\) must be even'):
      s.ContainsExactly('key1', 'value1', 'key2')

  def testContainsExactlyItemsIn(self):
    d1 = collections.OrderedDict(((2, 'two'), (4, 'four')))
    d2 = collections.OrderedDict(((2, 'two'), (4, 'four')))
    d3 = collections.OrderedDict(((4, 'four'), (2, 'two')))
    s = truth._DictionarySubject(d1)
    self.assertIsInstance(s.ContainsExactlyItemsIn(d2), truth._InOrder)
    self.assertIsInstance(s.ContainsExactlyItemsIn(d3), truth._NotInOrder)

    with self.Failure(
        "contains exactly <((2, 'two'),)>",
        "has unexpected items <[(4, 'four')]>",
        'often not the correct thing to do'):
      s.ContainsExactlyItemsIn({2: 'two'})

    with self.Failure(
        "contains exactly <((2, 'two'), (4, 'for'))>",
        "missing <[(4, 'for')]>",
        "has unexpected items <[(4, 'four')]>"):
      s.ContainsExactlyItemsIn({2: 'two', 4: 'for'})

    with self.Failure(
        "contains exactly <((2, 'two'), (4, 'four'), (5, 'five'))>",
        "missing <[(5, 'five')]>"):
      s.ContainsExactlyItemsIn({2: 'two', 4: 'four', 5: 'five'})

  def testOrderedDictIsEqualToUsesContainsExactlyItemsInPlusInOrder(self):
    d1 = collections.OrderedDict(((2, 'two'), (4, 'four')))
    d2 = collections.OrderedDict(((2, 'two'), (4, 'four')))
    d3 = collections.OrderedDict(((4, 'four'), (2, 'two')))
    s = truth._DictionarySubject(d1)
    s.IsEqualTo(d2)

    with self.Failure(
        'contains exactly', 'in order', "<((4, 'four'), (2, 'two'))>"):
      s.IsEqualTo(d3)

    with self.Failure(
        "contains exactly <((2, 'two'),)>",
        "has unexpected items <[(4, 'four')]>",
        'often not the correct thing to do'):
      s.IsEqualTo(collections.OrderedDict(((2, 'two'),)))

    with self.Failure(
        "contains exactly <((2, 'two'), (4, 'for'))>",
        "missing <[(4, 'for')]>",
        "has unexpected items <[(4, 'four')]>"):
      s.IsEqualTo(collections.OrderedDict(((2, 'two'), (4, 'for'))))

    with self.Failure(
        "contains exactly <((2, 'two'), (4, 'four'), (5, 'five'))>",
        "missing <[(5, 'five')]>"):
      s.IsEqualTo(collections.OrderedDict(
          ((2, 'two'), (4, 'four'), (5, 'five'))))

  def testDictIsEqualToUsesContainsExactlyItemsIn(self):
    d1 = {2: 'two', 4: 'four'}
    d2 = {2: 'two', 4: 'four'}
    d3 = collections.OrderedDict(((4, 'four'), (2, 'two')))
    s = truth._DictionarySubject(d1)
    s.IsEqualTo(d2)
    s.IsEqualTo(d3)

    with self.Failure(
        "contains exactly <((2, 'two'),)>",
        "has unexpected items <[(4, 'four')]>",
        'often not the correct thing to do'):
      s.IsEqualTo({2: 'two'})

    expected = {2: 'two', 4: 'for'}
    with self.Failure(
        'contains exactly <{0!r}>'.format(tuple(expected.items())),
        "missing <[(4, 'for')]>",
        "has unexpected items <[(4, 'four')]>"):
      s.IsEqualTo(expected)

    expected = {2: 'two', 4: 'four', 5: 'five'}
    with self.Failure(
        'contains exactly <{0!r}>'.format(tuple(expected.items())),
        "missing <[(5, 'five')]>"):
      s.IsEqualTo(expected)

  def testIsEqualToComparedWithNonDictionary(self):
    s = truth._DictionarySubject({2: 'two', 4: 'four'})
    with self.Failure('is equal to <3>'):
      s.IsEqualTo(3)
    with self.Failure('is equal to', 'DeclassifiedTestClass'):
      s.IsEqualTo(DeclassifiedTestClass())

  def testIsEqualToComparedWithDeclassifiedDictionary(self):
    s = truth._DictionarySubject(DeclassifiedDictTestClass())
    expected = DeclassifiedDictTestClass()
    s.IsEqualTo(expected)
    expected[3] = 'three'
    with self.Failure(
        "contains exactly <((3, 'three'),)>", "missing <[(3, 'three')]>"):
      s.IsEqualTo(expected)


class NumericSubjectTest(BaseTest):

  def testZero(self):
    s = truth._NumericSubject(0)
    s.IsZero()
    s.IsFinite()
    s.IsNotNan()
    with self.Failure('is non-zero'):
      s.IsNonZero()
    with self.Failure('should not have been finite'):
      s.IsNotFinite()
    with self.Failure('is equal to <inf>'):
      s.IsPositiveInfinity()
    with self.Failure('is equal to <-inf>'):
      s.IsNegativeInfinity()
    with self.Failure('is equal to <nan>'):
      s.IsNan()

  def testNonZero(self):
    s = truth._NumericSubject(10)
    s.IsNonZero()
    s.IsFinite()
    s.IsNotNan()
    with self.Failure('is zero'):
      s.IsZero()
    with self.Failure('should not have been finite'):
      s.IsNotFinite()
    with self.Failure('is equal to <inf>'):
      s.IsPositiveInfinity()
    with self.Failure('is equal to <-inf>'):
      s.IsNegativeInfinity()
    with self.Failure('is equal to <nan>'):
      s.IsNan()

  def testPositiveInfinity(self):
    s = truth._NumericSubject(truth.POSITIVE_INFINITY)
    s.IsNonZero()
    s.IsNotFinite()
    s.IsNotNan()
    s.IsPositiveInfinity()
    with self.Failure('is zero'):
      s.IsZero()
    with self.Failure('should have been finite'):
      s.IsFinite()
    with self.Failure('is equal to <-inf>'):
      s.IsNegativeInfinity()
    with self.Failure('is equal to <nan>'):
      s.IsNan()

  def testNegativeInfinity(self):
    s = truth._NumericSubject(truth.NEGATIVE_INFINITY)
    s.IsNonZero()
    s.IsNotFinite()
    s.IsNotNan()
    s.IsNegativeInfinity()
    with self.Failure('is zero'):
      s.IsZero()
    with self.Failure('should have been finite'):
      s.IsFinite()
    with self.Failure('is equal to <inf>'):
      s.IsPositiveInfinity()
    with self.Failure('is equal to <nan>'):
      s.IsNan()

  def testNan(self):
    s = truth._NumericSubject(truth.NAN)
    s.IsNonZero()
    s.IsNotFinite()
    s.IsNan()
    with self.Failure('is zero'):
      s.IsZero()
    with self.Failure('should have been finite'):
      s.IsFinite()
    with self.Failure('is equal to <inf>'):
      s.IsPositiveInfinity()
    with self.Failure('is equal to <-inf>'):
      s.IsNegativeInfinity()
    with self.Failure('should not have been <nan>'):
      s.IsNotNan()

  @mock.patch.object(
      truth, '_TolerantNumericSubject', return_value=mock.sentinel.FakeSubject)
  def testIsWithin(self, mock_subject):
    s = truth._NumericSubject(10)
    self.assertIs(s.IsWithin(0.1), mock.sentinel.FakeSubject)
    mock_subject.assert_called_once_with(10, 0.1, True)

  @mock.patch.object(
      truth, '_TolerantNumericSubject', return_value=mock.sentinel.FakeSubject)
  def testIsNotWithin(self, mock_subject):
    s = truth._NumericSubject(10)
    self.assertIs(s.IsNotWithin(0.1), mock.sentinel.FakeSubject)
    mock_subject.assert_called_once_with(10, 0.1, False)


class TolerantNumericSubjectTest(BaseTest):

  def testWithin(self):
    s = truth._TolerantNumericSubject(5.0, 0.1, True)
    s.Of(4.9)
    s.Of(5.0)
    s.Of(5.1)
    with self.Failure('should have been within <0.1> of each other'):
      s.Of(truth.NEGATIVE_INFINITY)
    with self.Failure('should have been within <0.1> of each other'):
      s.Of(4.8)
    with self.Failure('should have been within <0.1> of each other'):
      s.Of(5.2)
    with self.Failure('should have been within <0.1> of each other'):
      s.Of(truth.POSITIVE_INFINITY)

  def testNotWithin(self):
    s = truth._TolerantNumericSubject(5.0, 0.1, False)
    s.Of(truth.NEGATIVE_INFINITY)
    s.Of(4.8)
    s.Of(5.2)
    s.Of(truth.POSITIVE_INFINITY)
    with self.Failure('should not have been within <0.1> of each other'):
      s.Of(4.9)
    with self.Failure('should not have been within <0.1> of each other'):
      s.Of(5.0)
    with self.Failure('should not have been within <0.1> of each other'):
      s.Of(5.1)


class TolerantNumericSubjectToleranceTest(BaseTest, AllowUnresolvedSubjects):

  def testNegativeTolerance(self):
    s = truth._TolerantNumericSubject(0, -1, True)
    with self.AssertRaisesRegex(ValueError, r'cannot be negative'):
      s._CheckTolerance()

  def testPositiveInfinityTolerance(self):
    s = truth._TolerantNumericSubject(0, truth.POSITIVE_INFINITY, True)
    with self.AssertRaisesRegex(ValueError, r'cannot be positive infinity'):
      s._CheckTolerance()

  def testNegativeInfinityTolerance(self):
    s = truth._TolerantNumericSubject(0, truth.NEGATIVE_INFINITY, True)
    with self.AssertRaisesRegex(ValueError, r'cannot be negative'):
      s._CheckTolerance()

  def testNanTolerance(self):
    s = truth._TolerantNumericSubject(0, truth.NAN, True)
    with self.AssertRaisesRegex(ValueError, r'cannot be <nan>'):
      s._CheckTolerance()


class StringSubjectTest(BaseTest):

  def testNamedMultilineString(self):
    s = truth._StringSubject('line1\nline2').Named('string-name')
    self.assertEqual(s._GetSubject(), 'actual string-name')

  def testIsEqualToVerifiesEquality(self):
    s = truth._StringSubject('line1\nline2\n')
    s.IsEqualTo('line1\nline2\n')

  def testIsEqualToRaisesErrorWithVerboseDiff(self):
    s = truth._StringSubject('line1\nline2\nline3\nline4\nline5\n')
    with self.Failure('\n- line3\\n\n', '\n  line4\\n\n', '\n+ line6\\n\n'):
      s.IsEqualTo('line1\nline2\nline4\nline6\n')

  def testHasLength(self):
    s = truth._StringSubject('abc')
    s.HasLength(3)
    with self.Failure('has a length of 4', 'is 3'):
      s.HasLength(4)
    with self.Failure('has a length of 2', 'is 3'):
      s.HasLength(2)

  def testStartsWith(self):
    s = truth._StringSubject('abc')
    s.StartsWith('')
    s.StartsWith('a')
    s.StartsWith('ab')
    s.StartsWith('abc')
    with self.Failure("starts with <'b'>"):
      s.StartsWith('b')

  def testEndsWith(self):
    s = truth._StringSubject('abc')
    s.EndsWith('')
    s.EndsWith('c')
    s.EndsWith('bc')
    s.EndsWith('abc')
    with self.Failure("ends with <'b'>"):
      s.EndsWith('b')

  def testMatches(self):
    s = truth._StringSubject('abc')
    s.Matches('a')
    s.Matches(r'.b')
    s.Matches(re.compile(r'.b'))
    s.Matches(re.compile(r'A', re.I))
    with self.Failure('matches <d>'):
      s.Matches('d')
    with self.Failure('matches <b>'):
      s.Matches('b')

  def testDoesNotMatch(self):
    s = truth._StringSubject('abc')
    s.DoesNotMatch('b')
    s.DoesNotMatch('d')

    with self.Failure('fails to match <a>'):
      s.DoesNotMatch('a')
    with self.Failure('fails to match <.b>'):
      s.DoesNotMatch(re.compile(r'.b'))
    with self.Failure('fails to match <A>'):
      s.DoesNotMatch(re.compile(r'A', re.I))

  def testContainsMatch(self):
    s = truth._StringSubject('abc')
    s.ContainsMatch('a')
    s.ContainsMatch(re.compile(r'.b'))
    s.ContainsMatch(re.compile(r'A', re.I))
    s.ContainsMatch('b')
    with self.Failure('should have contained a match for <d>'):
      s.ContainsMatch('d')

  def testDoesNotContainMatch(self):
    s = truth._StringSubject('abc')
    s.DoesNotContainMatch('d')

    with self.Failure('should not have contained a match for <a>'):
      s.DoesNotContainMatch('a')
    with self.Failure('should not have contained a match for <b>'):
      s.DoesNotContainMatch('b')
    with self.Failure('should not have contained a match for <.b>'):
      s.DoesNotContainMatch(re.compile(r'.b'))
    with self.Failure('should not have contained a match for <A>'):
      s.DoesNotContainMatch(re.compile(r'A', re.I))


class NamedMockSubjectTest(BaseTest):

  @mock.patch('time.sleep')
  def testInitSetsName(self, mock_sleep):
    s = truth._NamedMockSubject(mock_sleep)
    self.assertEqual(s.name, 'sleep')

  @mock.patch('time.sleep')
  def testDefaultNameIsMock(self, mock_sleep):
    mock_sleep._mock_name = None
    s = truth._NamedMockSubject(mock_sleep)
    self.assertEqual(s.name, 'mock')

  def testMissingNameUsesDefaultName(self):
    s = truth._NamedMockSubject(object())
    self.assertEqual(s.name, 'mock')


class MockSubjectTest(BaseTest):

  ALL_CALLS = 'All calls: '

  @mock.patch('time.sleep')
  def testWasCalled(self, mock_sleep):
    s = truth._MockSubject(mock_sleep)
    with self.Failure(self.ALL_CALLS, '[]'):
      s.WasCalled()
    mock_sleep(10)
    s.WasCalled()

  @mock.patch('time.sleep')
  def testWasNotCalled(self, mock_sleep):
    s = truth._MockSubject(mock_sleep)
    s.WasNotCalled()
    mock_sleep(10)
    with self.Failure(self.ALL_CALLS, 'once', '[call(10)]'):
      s.WasNotCalled()
    mock_sleep(5)
    with self.Failure(self.ALL_CALLS, '2 times', '[call(10), call(5)]'):
      s.WasNotCalled()

  @mock.patch('time.sleep')
  def testHasCallsSingleCall(self, mock_sleep):
    s = truth._MockSubject(mock_sleep)
    with self.Failure():
      s.HasCalls(mock.call(10))
    with self.Failure():
      s.HasCalls([mock.call(10)])

    mock_sleep(10)
    self.assertIsInstance(s.HasCalls(mock.call(10)), truth._InOrder)
    self.assertIsInstance(s.HasCalls([mock.call(10)]), truth._InOrder)

  @mock.patch('time.sleep')
  def testHasCallsAnyOrderDefault(self, mock_sleep):
    s = truth._MockSubject(mock_sleep)
    mock_sleep(5)
    with self.Failure():
      s.HasCalls(mock.call(5), mock.call(10))
    with self.Failure():
      s.HasCalls([mock.call(5), mock.call(10)])

    mock_sleep(10)
    self.assertIsInstance(
        s.HasCalls(mock.call(5), mock.call(10)), truth._InOrder)
    self.assertIsInstance(
        s.HasCalls(mock.call(10), mock.call(5)), truth._NotInOrder)
    self.assertIsInstance(
        s.HasCalls([mock.call(5), mock.call(10)]), truth._InOrder)
    self.assertIsInstance(
        s.HasCalls([mock.call(10), mock.call(5)]), truth._NotInOrder)

  @mock.patch('time.sleep')
  def testHasCallsAnyOrderTrue(self, mock_sleep):
    s = truth._MockSubject(mock_sleep)
    mock_sleep(5)
    with self.Failure():
      s.HasCalls(mock.call(5), mock.call(10), any_order=True)
    with self.Failure():
      s.HasCalls([mock.call(5), mock.call(10)], any_order=True)

    mock_sleep(10)
    self.assertIsInstance(
        s.HasCalls(mock.call(5), mock.call(10), any_order=True),
        truth._InOrder)
    self.assertIsInstance(
        s.HasCalls([mock.call(5), mock.call(10)], any_order=True),
        truth._InOrder)
    self.assertIsInstance(
        s.HasCalls(mock.call(10), mock.call(5), any_order=True),
        truth._NotInOrder)
    self.assertIsInstance(
        s.HasCalls([mock.call(10), mock.call(5)], any_order=True),
        truth._NotInOrder)

    with self.Failure():
      s.HasCalls(mock.call(5), mock.call(7), any_order=True)
    with self.Failure():
      s.HasCalls(mock.call(7), mock.call(10), any_order=True)

    with self.Failure():
      s.HasCalls([mock.call(5), mock.call(7)], any_order=True)
    with self.Failure():
      s.HasCalls([mock.call(7), mock.call(10)], any_order=True)

  @mock.patch('time.sleep')
  def testHasCallsAnyOrderFalse(self, mock_sleep):
    s = truth._MockSubject(mock_sleep)
    mock_sleep(5)
    with self.Failure():
      s.HasCalls(mock.call(5), mock.call(10), any_order=False)
    with self.Failure():
      s.HasCalls([mock.call(5), mock.call(10)], any_order=False)

    mock_sleep(10)
    s.HasCalls(mock.call(5), mock.call(10), any_order=False)
    s.HasCalls([mock.call(5), mock.call(10)], any_order=False)

    with self.Failure():
      s.HasCalls(mock.call(10), mock.call(5), any_order=False)
    with self.Failure():
      s.HasCalls(mock.call(5), mock.call(7), any_order=False)
    with self.Failure():
      s.HasCalls(mock.call(7), mock.call(10), any_order=False)

    with self.Failure():
      s.HasCalls([mock.call(10), mock.call(5)], any_order=False)
    with self.Failure():
      s.HasCalls([mock.call(5), mock.call(7)], any_order=False)
    with self.Failure():
      s.HasCalls([mock.call(7), mock.call(10)], any_order=False)

  @mock.patch('time.sleep')
  def testHasExactlyCalls(self, mock_sleep):
    s = truth._MockSubject(mock_sleep)
    with self.Failure():
      s.HasExactlyCalls(mock.call(5))
    with self.Failure():
      s.HasExactlyCalls([mock.call(5)])

    mock_sleep(5)
    self.assertIsInstance(s.HasExactlyCalls(mock.call(5)), truth._InOrder)
    self.assertIsInstance(s.HasExactlyCalls([mock.call(5)]), truth._InOrder)

    mock_sleep(10)
    self.assertIsInstance(
        s.HasExactlyCalls(mock.call(5), mock.call(10)), truth._InOrder)
    self.assertIsInstance(
        s.HasExactlyCalls(mock.call(10), mock.call(5)), truth._NotInOrder)
    self.assertIsInstance(
        s.HasExactlyCalls([mock.call(5), mock.call(10)]), truth._InOrder)
    self.assertIsInstance(
        s.HasExactlyCalls([mock.call(10), mock.call(5)]), truth._NotInOrder)

    with self.Failure('unexpected items <[call(10)]>'):
      s.HasExactlyCalls(mock.call(5))
    with self.Failure('missing <[call(7)]>'):
      s.HasExactlyCalls(mock.call(5), mock.call(7), mock.call(10))
    with self.Failure('unexpected items <[call(10)]>'):
      s.HasExactlyCalls([mock.call(5)])
    with self.Failure('missing <[call(7)]>'):
      s.HasExactlyCalls([mock.call(5), mock.call(7), mock.call(10)])


class MockCalledSubjectTest(BaseTest):

  ALL_CALLS = 'All calls: '

  @mock.patch('time.sleep')
  def testOnce(self, mock_sleep):
    s = truth._MockCalledSubject(mock_sleep)
    with self.Failure(self.ALL_CALLS, 'once', '0 times', '[]'):
      s.Once()
    mock_sleep(10)
    s.Once()
    mock_sleep(10)
    with self.Failure(self.ALL_CALLS, 'once', '2 times',
                      '[call(10), call(10)]'):
      s.Once()

  @mock.patch('time.sleep')
  def testTimes(self, mock_sleep):
    s = truth._MockCalledSubject(mock_sleep)
    with self.Failure(self.ALL_CALLS, '2 times', '0 times', '[]'):
      s.Times(2)
    mock_sleep(10)
    with self.Failure(self.ALL_CALLS, '2 times', 'once', '[call(10)]'):
      s.Times(2)
    mock_sleep(10)
    s.Times(2)
    mock_sleep(10)
    with self.Failure(self.ALL_CALLS, '2 times', '3 times',
                      '[call(10), call(10), call(10)]'):
      s.Times(2)

  @mock.patch('time.sleep')
  def testWith(self, mock_sleep):
    s = truth._MockCalledSubject(mock_sleep)
    with self.Failure(self.ALL_CALLS, '[]'):
      s.With(10)
    mock_sleep(10)
    self.assertIsInstance(s.With(10), truth._MockCalledWithSubject)
    mock_sleep(5)
    self.assertIsInstance(s.With(5), truth._MockCalledWithSubject)
    self.assertIsInstance(s.With(10), truth._MockCalledWithSubject)

  @mock.patch('time.sleep')
  def testLastWith(self, mock_sleep):
    s = truth._MockCalledSubject(mock_sleep)
    with self.Failure(self.ALL_CALLS, '[]'):
      s.LastWith(10)
    mock_sleep(10)
    s.LastWith(10)
    mock_sleep(5)
    s.LastWith(5)
    with self.Failure(self.ALL_CALLS, '[call(10), call(5)]'):
      s.LastWith(10)


class MockCalledWithSubjectTest(BaseTest):

  ALL_CALLS = 'All calls: '

  @mock.patch('time.sleep')
  def testOnce(self, mock_sleep):
    s = truth._MockCalledWithSubject(mock_sleep, mock.call(5))
    with self.Failure(self.ALL_CALLS, 'once', '0 times', '[]'):
      s.Once()
    mock_sleep(5)
    s.Once()
    mock_sleep(10)
    s.Once()
    mock_sleep(5)
    with self.Failure(self.ALL_CALLS, 'once', '2 times',
                      '[call(5), call(10), call(5)]'):
      s.Once()

  @mock.patch('time.sleep')
  def testTimes(self, mock_sleep):
    s = truth._MockCalledWithSubject(mock_sleep, mock.call(5))
    with self.Failure(self.ALL_CALLS, '2 times', '0 times', '[]'):
      s.Times(2)
    mock_sleep(5)
    with self.Failure(self.ALL_CALLS, '2 times', 'once', '[call(5)]'):
      s.Times(2)
    mock_sleep(10)
    with self.Failure(self.ALL_CALLS, '2 times', 'once', '[call(5), call(10)]'):
      s.Times(2)
    mock_sleep(5)
    s.Times(2)
    mock_sleep(10)
    s.Times(2)
    mock_sleep(5)
    with self.Failure(self.ALL_CALLS, '2 times', '3 times',
                      '[call(5), call(10), call(5), call(10), call(5)]'):
      s.Times(2)


class NoneSubjectTest(BaseTest):

  def testSuccess(self):
    s = truth._NoneSubject(None)

    # DefaultSubject.
    s.IsNone()
    s.IsFalsy()
    s.IsEqualTo(None)
    s.IsNotEqualTo(0)
    s.IsNotEqualTo(False)
    s.IsNotEqualTo('')
    s.IsNotEqualTo(())
    s.IsIn((5, None, 'six'))
    s.IsNotIn((5, 'six'))
    s.IsAnyOf(5, None, 'six')
    s.IsNoneOf()
    s.IsNoneOf(5, 'six')
    s.IsInstanceOf(type(None))
    s.IsNotInstanceOf(int)
    s.IsSameAs(None)
    s.IsNotSameAs(0)
    s.HasAttribute('__class__')
    s.IsNotCallable()

    # ComparableSubject.
    if six.PY2:
      s.IsAtLeast(None)
      s.IsAtMost(None)

      for anything in (
          (), [], {}, 'str', u'str', object(), TestClass,
          truth.POSITIVE_INFINITY, truth.NEGATIVE_INFINITY, truth.NAN):
        s.IsAtMost(anything)
        s.IsLessThan(anything)
        # s.IsGreaterThan(...) will always fail, because None is less than
        # everything, except itself, which it is equal to.

  def testFailure(self):
    s = truth._NoneSubject(None)

    # DefaultSubject.
    with self.Failure('is not None'):
      s.IsNotNone()
    with self.Failure('is truthy'):
      s.IsTruthy()
    with self.Failure('is equal to <0>'):
      s.IsEqualTo(0)
    with self.Failure('is not equal to <None>'):
      s.IsNotEqualTo(None)
    with self.Failure("is equal to any of <(5, 'six')>"):
      s.IsIn((5, 'six'))
    with self.Failure('is not in (5, None)', 'found at index 1'):
      s.IsNotIn((5, None))
    with self.Failure("is equal to any of <(5, 'six')>"):
      s.IsAnyOf(5, 'six')
    with self.Failure('is not in (5, None)', 'found at index 1'):
      s.IsNoneOf(5, None)
    with self.Failure("is an instance of <<{0} 'int'>>".format(TYPE_WORD),
                      'NoneType'):
      s.IsInstanceOf(int)
    with self.Failure('expected not to be an instance of', 'NoneType'):
      s.IsNotInstanceOf(type(None))
    with self.Failure('is the same instance as <0>'):
      s.IsSameAs(0)
    with self.Failure('is not the same instance as <None>'):
      s.IsNotSameAs(None)
    with self.Failure("has attribute <'test_attribute'>"):
      s.HasAttribute('test_attribute')
    with self.Failure('is callable'):
      s.IsCallable()

    # ComparableSubject.
    if six.PY2:
      with self.Failure('is at least <0>'):
        s.IsAtLeast(0)
      # s.IsAtMost(...) will always succeed, because None is less than
      # everything, except itself, which it is equal to.
      with self.Failure('is greater than <None>'):
        s.IsGreaterThan(None)
      with self.Failure('is less than <None>'):
        s.IsLessThan(None)

    # BooleanSubject.
    with self.Failure('expected to be True, but was None'):
      s.IsTrue()
    with self.Failure('expected to be False, but was None'):
      s.IsFalse()

  def testInvalidOperation(self):
    self.s = truth._NoneSubject(None)
    self.AssertInvalidOperations({
        # ExceptionSubject.
        'HasMessage': ('error',),
        'HasMessageThat': (),
        'HasArgsThat': (),

        # ClassSubject.
        'IsSubclassOf': (type(None),),

        # IterableSubject.
        'HasSize': (1,),
        'IsEmpty': (),
        'IsNotEmpty': (),
        'Contains': (None,),
        'DoesNotContain': (5,),
        'ContainsNoDuplicates': (),
        'ContainsAllIn': ((None,),),
        'ContainsAllOf': (None,),
        'ContainsAnyIn': ((None,),),
        'ContainsAnyOf': (None,),
        'ContainsExactlyElementsIn': ((None,),),
        'ContainsNone': ((5,),),
        'ContainsNoneOf': (5,),
        'IsOrdered': (),
        'IsOrderedAccordingTo': (truth.Cmp,),
        'IsStrictlyOrdered': (),
        'IsStrictlyOrderedAccordingTo': (truth.Cmp,),

        # DictionarySubject.
        'ContainsKey': ('key',),
        'DoesNotContainKey': ('key',),
        'ContainsItem': ('key', 'value'),
        'DoesNotContainItem': ('key', 'value'),
        'ContainsExactly': ('key', 'value'),
        'ContainsExactlyItemsIn': ({'key': 'value'},),

        # NumericSubject.
        'IsWithin': (0.1,),
        'IsNotWithin': (0.1,),

        # StringSubject.
        'HasLength': (0,),
        'StartsWith': ('',),
        'EndsWith': ('',),
        'Matches': ('',),
        'DoesNotMatch': ('',),
        'ContainsMatch': ('',),
        'DoesNotContainMatch': ('',),

        # MockSubject.
        'WasCalled': (),
        'WasNotCalled': (),
        'HasCalls': ([],),

        # We don't need to test secondary subjects like _InOrder because the
        # above subjects would have already derailed the assertion train.
    })

  @mock.patch.object(six, 'PY2', new=False)
  def testPython3InequalityFailure(self):
    self.s = truth._NoneSubject(None)
    self.AssertInvalidOperations({
        'IsAtLeast': (None,),
        'IsAtMost': (None,),
        'IsGreaterThan': (None,),
        'IsLessThan': (None,),
        'IsWithin': (0.1,),
        'IsNotWithin': (0.1,)
    })

  def AssertInvalidOperations(self, operations):
    for name, args in six.iteritems(operations):
      with self.Failure(
          'Invalid operation on None subject: <{0}>'.format(name)):
        getattr(self.s, name)(*args)


class TypeConstructorTest(absltest.TestCase):

  def testAssertNoKeyIsASubclassOfAnother(self):
    keys = list(truth._TYPE_CONSTRUCTORS.keys())
    for k1 in six.moves.xrange(len(keys) - 1):
      for k2 in six.moves.xrange(k1 + 1, len(keys)):
        self.assertFalse(
            issubclass(keys[k1], keys[k2]),
            msg='{0} is a subclass of {1}'.format(keys[k1], keys[k2]))
        self.assertFalse(
            issubclass(keys[k2], keys[k1]),
            msg='{0} is a subclass of {1}'.format(keys[k2], keys[k1]))


if __name__ == '__main__':
  absltest.main()
