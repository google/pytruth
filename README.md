<!---
Copyright 2017 Google Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
--->

# PyTruth: Truth in Python

Provides unittest assertions in a fluent style.
Translated from the Java implementation,
[google/truth](https://github.com/google/truth).

## License

PyTruth is licensed under the [Apache 2.0 license](LICENSE).

## Disclaimer

PyTruth is not an official Google product.

## Contributing

Please see the [guidelines for contributing](CONTRIBUTING.md)
before creating pull requests.

## Support

PyTruth is not an actively maintained project. No support is provided.

It is shared with the community to bring an expressive, consistent assertion
style to projects that may be using a combination of
[unittest](https://docs.python.org/3/library/unittest.html),
[googletest](https://github.com/google/googletest),
[mox](https://pypi.python.org/pypi/mox), and
[mock](https://docs.python.org/3/library/unittest.mock.html)&mdash;especially
to people familiar with [Java Truth](https://github.com/google/truth).

User group:
[pytruth-users@googlegroups.com](https://groups.google.com/d/forum/pytruth-users)

## Overview

Import the `truth` module and alias the `AssertThat()` method to begin asserting
things:

```
from truth.truth import AssertThat
```

Then, instead of writing

```
self.assertEqual(a, b)
self.assertTrue(c)
self.assertIn(a, d)
self.assertTrue(a in d and b in d)
self.assertTrue(a in d or b in d or c in d)
with self.assertRaises(Error):
  Explode()
```

one would write

```
AssertThat(a).IsEqualTo(b)
AssertThat(c).IsTrue()
AssertThat(d).Contains(a)
AssertThat(d).ContainsAllOf(a, b)
AssertThat(d).ContainsAnyOf(a, b, c)
with AssertThat(Error).IsRaised():
  Explode()
```

Tests should be easier to read and write, and flow more clearly.

## Limitations

unittest assertions accept a `msg` parameter to display if the assertion fails.
PyTruth has no such mechanism, though its failure messages tend to be more
informative.

The type of the subject under test (the parameter passed to `AssertThat()`) will
not be known until runtime, unlike Java where the type is known at compile time.
IDEs may not correctly autocomplete available predicates on an asserted subject.

In Python 2, `None` compares less than every other thing, except `None` itself.
`None` is less than `nan`, and it is less than negative infinity. Therefore, use
caution when a function might return `None`. The assertion
`AssertThat(Func()).IsLessThan(0)` succeeds whether `Func()` returns a negative
number or `None`. Instead, first check the `None`-ness of the return value with
`IsNone()` or `IsNotNone()` before performing an inequality assertion.

In Python 3, `None` is no longer comparable using `<` `>` `<=` `>=`.
PyTruth detects the version of the Python interpreter and compares or fails
appropriately, rather than allowing Python 3's `TypeError` to bubble up.

If the iterator over a shared value (either expected or actual) changes that
value or its underlying elements, the behavior is undefined:
all, none, or some of the assertions may succeed or fail, arbitrarily.

This library is threadsafe; you may execute multiple assertions in parallel.

## Conversion Recipes

### General
unittest                     | PyTruth
-----------------------------|----------------------------------------
`assertEqual(a, b)`          | `AssertThat(a).IsEqualTo(b)`
`assertNotEqual(a, b)`       | `AssertThat(a).IsNotEqualTo(b)`
`assertTrue(a)`              | `AssertThat(a).IsTruthy()`
`assertFalse(a)`             | `AssertThat(a).IsFalsy()`
`assertIs(a, True)`          | `AssertThat(a).IsTrue()`
`assertIs(a, False)`         | `AssertThat(a).IsFalse()`
`assertIs(a, b)`             | `AssertThat(a).IsSameAs(b)`
`assertIsNot(a, b)`          | `AssertThat(a).IsNotSameAs(b)`
`assertIsNone(a)`            | `AssertThat(a).IsNone()`
`assertIsNotNone(a)`         | `AssertThat(a).IsNotNone()`
`assertIn(a, b)`             | `AssertThat(a).IsIn(b)`
`assertIn(a, [b, c, d])`     | `AssertThat(a).IsAnyOf(b, c, d)`
`assertNotIn(a, b)`          | `AssertThat(a).IsNotIn(b)`
`assertNotIn(a, [b, c, d])`  | `AssertThat(a).IsNoneOf(b, c, d)`
`assertIsInstance(a, b)`     | `AssertThat(a).IsInstanceOf(b)`
`assertIsNotInstance(a, b)`  | `AssertThat(a).IsNotInstanceOf(b)`
`assertTrue(hasattr(a, b))`  | `AssertThat(a).HasAttribute(b)`
`assertFalse(hasattr(a, b))` | `AssertThat(a).DoesNotHaveAttribute(b)`
`assertTrue(callable(a))`    | `AssertThat(a).IsCallable()`
`assertFalse(callable(a))`   | `AssertThat(a).IsNotCallable()`

#### Truthiness

PyTruth supports a finer grained distinction of truthiness than unittest does.
In particular, it differentiates between "is `True`" and "is *truthy*."
unittest's `assertTrue(x)` is equivalent to `assertIs(bool(x), True)`,
and its `assertFalse(x)` is equivalent to `assertIs(bool(x), False)`.
PyTruth's `IsTrue()` and `IsFalse()` predicates match *only* the boolean
subjects `True` and `False` themselves.
Therefore it is important not to blindly convert `assertTrue()` to `IsTrue()`,
and likewise with `assertFalse()` and `IsFalse()`.

Truthy assertion              | Result   | Falsy assertion               | Result
------------------------------|----------|-------------------------------|---------
`assertTrue(True)`            | succeeds | `assertFalse(False)`          | succeeds
`assertTrue(1)`               | succeeds | `assertFalse(0)`              | succeeds
`assertTrue(None)`            | fails    | `assertFalse(None)`           | succeeds
`AssertThat(True).IsTrue()`   | succeeds | `AssertThat(False).IsFalse()` | succeeds
`AssertThat(1).IsTrue()`      | fails    | `AssertThat(0).IsFalse()`     | fails
`AssertThat(None).IsTrue()`   | fails    | `AssertThat(None).IsFalse()`  | fails
`AssertThat(True).IsTruthy()` | succeeds | `AssertThat(False).IsFalsy()` | succeeds
`AssertThat(1).IsTruthy()`    | succeeds | `AssertThat(0).IsFalsy()`     | succeeds
`AssertThat(None).IsTruthy()` | fails    | `AssertThat(None).IsFalsy()`  | succeeds

### Strings
unittest                                                       | PyTruth
---------------------------------------------------------------|---------------------------------------
`assertEqual(len(s), n)`                                       | `AssertThat(s).HasLength(n)`
`assertTrue(s.startswith('a'))`                                | `AssertThat(s).StartsWith('a')`
`assertTrue(s.endswith('a'))`                                  | `AssertThat(s).EndsWith('a')`
`assertRegex(s, r)`<br>`assertRegexpMatches(s, r)`             | `AssertThat(s).ContainsMatch(r)`
`assertNotRegex(s, r)`<br>`assertNotRegexpMatches(s, r)`       | `AssertThat(s).DoesNotContainMatch(r)`
`assertRegex(s, '^r')`<br>`assertRegexpMatches(s, '^r')`       | `AssertThat(s).Matches('r')`
`assertNotRegex(s, '^r')`<br>`assertNotRegexpMatches(s, '^r')` | `AssertThat(s).DoesNotMatch('r')`

#### Matching strings

The `r` parameter passed to the matching functions may either be a
`r'raw string'`, or a pattern object returned from `re.compile()`.

### Numbers, strings, and other comparable things
unittest                   | PyTruth
---------------------------|---------------------------------
`assertLess(a, b)`         | `AssertThat(a).IsLessThan(b)`
`assertGreater(a, b)`      | `AssertThat(a).IsGreaterThan(b)`
`assertLessEqual(a, b)`    | `AssertThat(a).IsAtMost(b)`
`assertGreaterEqual(a, b)` | `AssertThat(a).IsAtLeast(b)`

### Numbers
unittest                              | PyTruth
--------------------------------------|-------------------------------------
`assertEqual(a, 0)`                   | `AssertThat(a).IsZero()`
`assertNotEqual(a, 0)`                | `AssertThat(a).IsNonZero()`
`assertEqual(a, float('inf'))`        | `AssertThat(a).IsPositiveInfinity()`
`assertEqual(a, float('-inf'))`       | `AssertThat(a).IsNegativeInfinity()`
`assertFalse(a.isinf() or a.isnan())` | `AssertThat(a).IsFinite()`
`assertTrue(a.isnan())`               | `AssertThat(a).IsNan()`
`assertFalse(a.isnan())`              | `AssertThat(a).IsNotNan()`
`assertAlmostEqual(a, b, delta=d)`    | `AssertThat(a).IsWithin(d).Of(b)`
`assertNotAlmostEqual(a, b, delta=d)` | `AssertThat(a).IsNotWithin(d).Of(b)`

### Lists, strings, and other iterables
unittest                        | PyTruth
--------------------------------|---------------------------------------------
`assertEqual(len(a), n)`        | `AssertThat(a).HasSize(n)`
`assertEqual(len(a), 0)`        | `AssertThat(a).IsEmpty()`
`assertGreaterThan(len(a), 0)`  | `AssertThat(a).IsNotEmpty()`
`assertIn(b, a)`                | `AssertThat(a).Contains(b)`
`assertNotIn(b, a)`             | `AssertThat(a).DoesNotContain(b)`
`assertTrue(b in a and c in a)` | `AssertThat(a).ContainsAllOf(b, c)`<br>`AssertThat(a).ContainsAllIn([b, c])`
`assertTrue(b in a or c in a)`  | `AssertThat(a).ContainsAnyOf(b, c)`<br>`AssertThat(a).ContainsAnyIn([b, c])`
`assertTrue(b in a and c in a and len(a) == 2)`      | `AssertThat(a).ContainsExactly(b, c)`
`assertCountEqual(a, b)`<br>`assertItemsEqual(a, b)` | `AssertThat(sorted(a)).ContainsExactlyElementsIn(sorted(b)).InOrder()`
`assertTrue(b not in a and c not in a)`              | `AssertThat(a).ContainsNoneOf(b, c)`<br>`AssertThat(a).ContainsNoneIn([b, c])`
N/A                             | `AssertThat(a).ContainsNoDuplicates()`
N/A                             | `AssertThat(a).IsOrdered()`
N/A                             | `AssertThat(a).IsOrderedAccordingTo(cf)`
N/A                             | `AssertThat(a).IsStrictlyOrdered()`
N/A                             | `AssertThat(a).IsStrictlyOrderedAccordingTo(cf)`

#### Defining order

The `cf` parameter passed to `IsOrderedAccordingTo()` and
`IsStrictlyOrderedAccordingTo()` should be a callable that follows the contract
of `cmp(x, y)`: it should return negative if x < y, zero if x == y,
and positive if x > y.

*Ordered* means that the iterable's elements must increase (or decrease,
depending on `cf`) from beginning to end. Adjacent elements are allowed to be
equal. *Strictly ordered* means that in addition, the elements must be unique
(*i.e.*, monotonically increasing or decreasing).

`IsOrdered()` is equivalent to `IsOrderedAccordingTo(cmp)`.

`IsStrictlyOrdered()` is equivalent to `IsStrictlyOrderedAccordingTo(cmp)`.

#### Asserting order

By default, `ContainsAll...` and `ContainsExactly...` do not enforce that the
order of the elements in the subject under test matches the that of the expected
value. To do that, append `InOrder()` to the returned predicate.

Containment assertion                                      | Result
-----------------------------------------------------------|---------
`AssertThat([2, 4, 6]).ContainsAllOf(6, 2)`                | succeeds
`AssertThat([2, 4, 6]).ContainsAllOf(6, 2).InOrder()`      | fails
`AssertThat([2, 4, 6]).ContainsAllOf(2, 6).InOrder()`      | succeeds
`AssertThat([2, 4, 6]).ContainsExactly(2, 6, 4)`           | succeeds
`AssertThat([2, 4, 6]).ContainsExactly(2, 6, 4).InOrder()` | fails
`AssertThat([2, 4, 6]).ContainsExactly(2, 4, 6).InOrder()` | succeeds

When using `InOrder()`, ensure that both the subject under test and the expected
value have a predictable order, otherwise the result is undefined. For example,
`AssertThat(list_a).ContainsExactlyElementsIn(set_a).InOrder()`
may or may not succeed, depending on how the `set` implements ordering.

### Dictionaries, in addition to the table above
unittest                           | PyTruth
-----------------------------------|------------------------------------------------
`assertIn(k, d)`                   | `AssertThat(d).ContainsKey(k)`
`assertNotIn(k, d)`                | `AssertThat(d).DoesNotContainKey(k)`
`assertIn((k, v), d.items())`      | `AssertThat(d).ContainsItem(k, v)`
`assertNotIn((k, v), d.items())`   | `AssertThat(d).DoesNotContainItem(k, v)`
`assertEqual(d, {k1: v1, k2: v2})` | `AssertThat(d).ContainsExactly(k1, v1, k2, v2)`
`assertEqual(d1, d2)`              | `AssertThat(d1).ContainsExactlyItemsIn(d2)`
`assertDictContainsSubset(d1, d2)` | `AssertThat(d1.items()).ContainsAllIn(d2.items())`

### Exceptions
unittest                                | PyTruth
----------------------------------------|-------------------------------------------------
`with assertRaises(e):`                 | `with AssertThat(e).IsRaised():`
`with assertRaisesRegex(e, r):`         | `with AssertThat(e).IsRaised(matching=r):`
N/A                                     | `with AssertThat(e).IsRaised(containing='a'):`
`assertEqual(e.message, m)`             | `AssertThat(e).HasMessage(m)`
`assertTrue(e.message.startswith('a'))` | `AssertThat(e).HasMessageThat().StartsWith('a')`
`assertIn(a, e.args)`                   | `AssertThat(e).HasArgsThat().Contains(a)`

#### Matching raised exceptions

When expecting an exception using the `AssertThat(e).IsRaised()` context, any
exception raised whose type is equal to `e` or a subclass of `e` is accepted.
If an exception is raised that is not a subclass of `e`, the assertion fails.

The `e` parameter in the `AssertThat(e).IsRaised()` context may be either an
exception *class* like `ValueError`, or it may be an exception *instance* like
`ValueError('some error')`. If an instance is passed, then any exception raised
by the code under test must also have matching `message` and `args` properties,
in addition to being a subclass of the expected exception.

### Mocked functions
unittest                                            | PyTruth
----------------------------------------------------|-------------------------------------------------
`m.assert_called()`                                 | `AssertThat(m).WasCalled()`
`m.assert_not_called()`                             | `AssertThat(m).WasNotCalled()`
`m.assert_called_once()`                            | `AssertThat(m).WasCalled().Once()`
`assertEqual(m.call_count, n)`                      | `AssertThat(m).WasCalled().Times(n)`
`m.assert_called_with(*a, **k)`                     | `AssertThat(m).WasCalled().LastWith(*a, **k)`
`m.assert_called_once_with(*a, **k)`                | `AssertThat(m).WasCalled().Once().With(*a, **k)`
N/A                                                 | `AssertThat(m).WasCalled().With(*a, **k).Once()`
`m.assert_has_calls(calls,`&nbsp;`any_order=True)`  | `AssertThat(m).HasCalls(calls)`
`m.assert_has_calls(calls,`&nbsp;`any_order=False)` | `AssertThat(m).HasCalls(calls).InOrder()`
N/A                                                 | `AssertThat(m).HasExactlyCalls(c1, c2)`
N/A                                                 | `AssertThat(m).HasExactlyCalls(c1, c2).InOrder()`
`m.assert_any_call(*a, **k)`                        | `AssertThat(m).WasCalled().With(*a, **k)`

#### Being called once, with arguments

The `WasCalled().Once().With(...)` and `WasCalled().With(...).Once()` assertions
are subtly different. `WasCalled().Once().With(...)` asserts that the function
was called one time ever, and that one time it was called, it was passed those
arguments. `WasCalled().With(...).Once()` asserts that the function was passed
those arguments exactly once, but it is permitted to have been called with
other, irrelevant arguments. Thus, `WasCalled().Once().With(...)` is the
stricter assertion. Consider using `HasExactlyCalls()` for more clarity.

### Classes
unittest                      | PyTruth
------------------------------|--------------------------------
`assertTrue(a.issubclass(b))` | `AssertThat(a).IsSubclassOf(b)`
