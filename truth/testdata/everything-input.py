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

"""File for convert.py testing all assertions."""

# pylint: disable=bad-continuation
# pylint: disable=line-too-long
# pylint: disable=undefined-variable

self.assertEqual(equal_a0, equal_b0)
self.assertEqual(equal_t0, True)
self.assertEqual(equal_f0, False)
self.assertEqual(equal_n0, None)
self.assertEqual(equal_n1, 26)
self.assertEqual(27, equal_n2)
self.assertEqual(equal_n3, 2.8)
self.assertEqual(equal_n4, -29)
self.assertEqual(equal_n5, 30L)
self.assertEqual(equal_n6, -3.1)
self.assertEqual(equal_z0, 0)
self.assertEqual(0, equal_z1)
self.assertEqual(equal_m0, function_call())

self.assertEqual(equal_long_method(arg0, (tuple_e0, tuple_e1),
                                   [list(list_e0, list_e1)]),
                 equal_long_method({dict_k0: dict_v0,
                                    dict_k1: (tuple_e0, tuple_e1)}))

self.assertEqual(equal_ra0, 'equal_rb0')
self.assertEqual('equal_rb1', equal_ra1)
self.assertEqual(equal_ra2, "equal_rb2")
self.assertEqual("equal_rb3", equal_ra3)
self.assertEqual(actual_ra4, equal_rb4)
self.assertEqual(equal_rb5, actual_ra5)
self.assertEqual(equal_ra6, expected_rb6)
self.assertEqual(expected_rb7, equal_ra7)
self.assertEqual(result_ra8, equal_rb8)
self.assertEqual(equal_rb9, result_ra9)
self.assertEqual(os.environ['ENV0'], equal_rba)
self.assertEqual(equal_rbb, os.environ['ENV1'])
self.assertEqual(os.environ.get('ENV2'), equal_rbc)
self.assertEqual(equal_rbd, os.environ.get('ENV3'))
self.assertEqual(len(equal_rae), 55)
self.assertEqual(56, len(equal_raf))
self.assertEqual(len(equal_rag), 0)
self.assertEqual(0, len(equal_rah))

self.assertEqual(equal_e0, '')
self.assertEqual(equal_e1, "")
self.assertEqual(equal_e2, r'')
self.assertEqual(equal_e3, r"")
self.assertEqual(equal_e4, u'')
self.assertEqual(equal_e5, u"")
self.assertEqual(equal_e6, ())
self.assertEqual(equal_e7, [])
self.assertEqual(equal_e8, {})
self.assertEqual(equal_e9, dict())
self.assertEqual(equal_ea, list())
self.assertEqual(equal_eb, set())
self.assertEqual(equal_ec, tuple())
self.assertEqual(equal_ed, collections.OrderedDict())
self.assertEqual('', equal_ee)
self.assertEqual("", equal_ef)
self.assertEqual(r'', equal_eg)
self.assertEqual(r"", equal_eh)
self.assertEqual(u'', equal_ei)
self.assertEqual(u"", equal_ej)
self.assertEqual((), equal_ek)
self.assertEqual([], equal_el)
self.assertEqual({}, equal_em)
self.assertEqual(dict(), equal_en)
self.assertEqual(list(), equal_eo)
self.assertEqual(set(), equal_ep)
self.assertEqual(tuple(), equal_eq)
self.assertEqual(collections.OrderedDict(), equal_er)

self.assertEqual(equal_l0, [equal_b0, equal_c0])
self.assertEqual(equal_l1, (equal_b1, equal_c1))
self.assertEqual([equal_b2, equal_c2], equal_l2)
self.assertEqual((equal_b3, equal_c3), equal_l3)
self.assertEqual(equal_l4, [equal_b4 for equal_c4 in equal_d4])
self.assertEqual(equal_l5, (equal_b5 for equal_c5 in equal_d5))
self.assertEqual(equal_l6, {equal_b6 for equal_c6 in equal_d6})
self.assertEqual(equal_l7, [equal_b7])
self.assertEqual([equal_b8 for equal_c8 in equal_d8], equal_l8)
self.assertEqual((equal_b9 for equal_c9 in equal_d9), equal_l9)
self.assertEqual({equal_ba for equal_ca in equal_da}, equal_la)
self.assertEqual([equal_bb], equal_lb)

self.assertDictContainsSubset(dict_subset_a0, dict_subset_b0)

self.assertDictEqual(dict_equal_a0, dict_equal_b0)
self.assertDictEqual(dict_equal_e0, {})
self.assertDictEqual(dict_equal_e1, dict())
self.assertDictEqual(dict_equal_e2, collections.OrderedDict())
self.assertDictEqual({}, dict_equal_e3)
self.assertDictEqual(dict(), dict_equal_e4)
self.assertDictEqual(collections.OrderedDict(), dict_equal_e5)
self.assertDictEqual(dict_equal_a6, {dict_equal_b6: dict_equal_c6})
self.assertDictEqual({dict_equal_b7: dict_equal_c7}, dict_equal_a7)

self.assertCountEqual(count_equal_a0, count_equal_b0)
self.assertCountEqual(count_equal_a1, [count_equal_b1, count_equal_c1])
self.assertCountEqual(count_equal_a2, (count_equal_b2, count_equal_c2))
self.assertCountEqual([count_equal_b3, count_equal_c3], count_equal_a3)
self.assertCountEqual((count_equal_b4, count_equal_c4), count_equal_a4)
self.assertCountEqual(count_equal_a5, [count_equal_b5])

self.assertItemsEqual(items_equal_a0, items_equal_b0)
self.assertItemsEqual(items_equal_a1, [items_equal_b1, items_equal_c1])
self.assertItemsEqual(items_equal_a2, (items_equal_b2, items_equal_c2))
self.assertItemsEqual([items_equal_b3, items_equal_c3], items_equal_a3)
self.assertItemsEqual((items_equal_b4, items_equal_c4), items_equal_a4)
self.assertItemsEqual(items_equal_a5, [items_equal_b5])

self.assertListEqual(list_equal_a0, list_equal_b0)
self.assertListEqual(list_equal_l1, [list_equal_b1, list_equal_c1])
self.assertListEqual([list_equal_b2, list_equal_c2], list_equal_l2)
self.assertListEqual(list_equal_l3, [list_equal_b3])

self.assertSequenceEqual(sequence_equal_a0, sequence_equal_b0)
self.assertSequenceEqual(sequence_equal_a1, [sequence_equal_b1, sequence_equal_c1])
self.assertSequenceEqual(sequence_equal_a2, (sequence_equal_b2, sequence_equal_c2))
self.assertSequenceEqual([sequence_equal_b3, sequence_equal_c3], sequence_equal_a3)
self.assertSequenceEqual((sequence_equal_b4, sequence_equal_c4), sequence_equal_a4)
self.assertSequenceEqual(sequence_equal_a5, [sequence_equal_b5])

self.assertSetEqual(set_equal_a0, set_equal_b0)
self.assertSetEqual(set_equal_a1, {set_equal_b1, set_equal_c1})
self.assertSetEqual({set_equal_b2, set_equal_c2}, set_equal_a2)

self.assertTupleEqual(tuple_equal_a0, tuple_equal_b0)
self.assertTupleEqual(tuple_equal_a1, (tuple_equal_b1, tuple_equal_c1))
self.assertTupleEqual((tuple_equal_b2, tuple_equal_c2), tuple_equal_a2)

self.assertSameElements(same_elements_a0, same_elements_b0)
self.assertSameElements(same_elements_a1, [same_elements_b1, same_elements_c1])
self.assertSameElements(same_elements_a2, (same_elements_b2, same_elements_c2))
self.assertSameElements([same_elements_b3, same_elements_c3], same_elements_a3)
self.assertSameElements((same_elements_b4, same_elements_c4), same_elements_a4)
self.assertSameElements(same_elements_a5, [same_elements_b5])

self.assertEquals(equal_a1, equal_b1)

self.assertNotEqual(not_equal_a0, not_equal_b0)
self.assertNotEquals(not_equal_a1, not_equal_b1)
self.assertNotEqual(not_equal_t0, True)
self.assertNotEqual(not_equal_f0, False)
self.assertNotEqual(not_equal_n0, None)
self.assertNotEqual(not_equal_n1, 138)
self.assertNotEqual(139, not_equal_n2)
self.assertNotEqual(not_equal_n3, 14.0)
self.assertNotEqual(not_equal_n4, -141)
self.assertNotEqual(not_equal_n5, 142L)
self.assertNotEqual(not_equal_n6, -14.3)
self.assertNotEqual(not_equal_z0, 0)
self.assertNotEqual(0, not_equal_z1)
self.assertNotEqual(not_equal_m0, function_call())

self.assertNotEqual(not_equal_ra0, 'not_equal_rb0')
self.assertNotEqual('not_equal_rb1', not_equal_ra1)
self.assertNotEqual(not_equal_ra2, "not_equal_rb2")
self.assertNotEqual("not_equal_rb3", not_equal_ra3)
self.assertNotEqual(actual_ra4, not_equal_rb4)
self.assertNotEqual(not_equal_rb5, actual_ra5)
self.assertNotEqual(not_equal_ra6, expected_rb6)
self.assertNotEqual(expected_rb7, not_equal_ra7)
self.assertNotEqual(result_ra8, not_equal_rb8)
self.assertNotEqual(not_equal_rb9, result_ra9)
self.assertNotEqual(os.environ['ENV0'], not_equal_rba)
self.assertNotEqual(not_equal_rbb, os.environ['ENV1'])
self.assertNotEqual(os.environ.get('ENV2'), not_equal_rbc)
self.assertNotEqual(not_equal_rbd, os.environ.get('ENV3'))
self.assertNotEqual(len(not_equal_rae), 162)
self.assertNotEqual(163, len(not_equal_raf))
self.assertNotEqual(len(not_equal_rag), 0)
self.assertNotEqual(0, len(not_equal_rah))

self.assertNotEqual(not_equal_e0, '')
self.assertNotEqual(not_equal_e1, "")
self.assertNotEqual(not_equal_e2, r'')
self.assertNotEqual(not_equal_e3, r"")
self.assertNotEqual(not_equal_e4, u'')
self.assertNotEqual(not_equal_e5, u"")
self.assertNotEqual(not_equal_e6, ())
self.assertNotEqual(not_equal_e7, [])
self.assertNotEqual(not_equal_e8, {})
self.assertNotEqual(not_equal_e9, dict())
self.assertNotEqual(not_equal_ea, list())
self.assertNotEqual(not_equal_eb, set())
self.assertNotEqual(not_equal_ec, tuple())
self.assertNotEqual(not_equal_ed, collections.OrderedDict())
self.assertNotEqual('', not_equal_ee)
self.assertNotEqual("", not_equal_ef)
self.assertNotEqual(r'', not_equal_eg)
self.assertNotEqual(r"", not_equal_eh)
self.assertNotEqual(u'', not_equal_ei)
self.assertNotEqual(u"", not_equal_ej)
self.assertNotEqual((), not_equal_ek)
self.assertNotEqual([], not_equal_el)
self.assertNotEqual({}, not_equal_em)
self.assertNotEqual(dict(), not_equal_en)
self.assertNotEqual(list(), not_equal_eo)
self.assertNotEqual(set(), not_equal_ep)
self.assertNotEqual(tuple(), not_equal_eq)
self.assertNotEqual(collections.OrderedDict(), not_equal_er)

self.assert_(underscore)

self.assertTrue(true_a0)

self.assertFalse(false_a0)

self.assertLess(less_a0, less_b0)
self.assertLess(less_a1, 203)
self.assertLess(204, less_a2)

self.assertLessEqual(less_equal_a0, less_equal_b0)
self.assertLessEqual(less_equal_a1, 207)
self.assertLessEqual(208, less_equal_a2)

self.assertGreater(greater_a0, greater_b0)
self.assertGreater(greater_a1, 211)
self.assertGreater(212, greater_a2)

self.assertGreaterEqual(greater_equal_a0, greater_equal_b0)
self.assertGreaterEqual(greater_equal_a1, 215)
self.assertGreaterEqual(216, greater_equal_a2)

self.assertIs(is_a0, is_b0)

self.assertIsNot(is_not_a0, is_not_b0)

self.assertIsNone(is_none_a0)

self.assertIsNotNone(is_not_none_a0)

self.assertIsInstance(is_instance_a0, is_instance_b0)

self.assertNotIsInstance(is_not_instance_a0, is_not_instance_b0)

self.assertIn(in_a0, in_b0)
self.assertIn(in_a1, [in_b1, in_c1])
self.assertIn(in_a2, (in_b2, in_c2))

self.assertNotIn(not_in_a0, not_in_b0)
self.assertNotIn(not_in_a1, [not_in_b1, not_in_c1])
self.assertNotIn(not_in_a2, (not_in_b2, not_in_c2))

self.assertTrue(starts_a0.startswith('starts_b0'))
self.assertTrue(starts_a1.startswith("starts_b1"))
self.assertTrue(starts_a2.startswith(r'starts_b2'))
self.assertTrue(starts_a3.startswith(u"starts_b3"))
self.assertTrue(starts_a4.startswith(r"starts_b4"))
self.assertTrue(starts_a5.startswith(u'starts_b5'))

self.assertTrue(ends_a0.endswith('ends_b0'))
self.assertTrue(ends_a1.endswith("ends_b1"))
self.assertTrue(ends_a2.endswith(r'ends_b2'))
self.assertTrue(ends_a3.endswith(u"ends_b3"))
self.assertTrue(ends_a4.endswith(r"ends_b4"))
self.assertTrue(ends_a5.endswith(u'ends_b5'))

self.assertRegex(regex_a0, regex_b0)

self.assertRegexpMatches(regexp_matches_a0, regexp_matches_b0)

self.assertNotRegex(not_regex_a0, not_regex_b0)

self.assertNotRegexpMatches(not_regexp_matches_a0, not_regexp_matches_b0)

with self.assertRaises(raises_a0):
  MethodThatRaises()

self.assertRaises(raises_a1, MethodThatRaises)

self.assertRaises(raises_a2, MethodThatRaises, raises_b2, raises_c2)

with self.assertRaisesRegexp(raises_regexp_a0, raises_regexp_b0):
  MethodThatRaisesRegexp()

self.assertRaisesRegexp(
    raises_regexp_a1, raises_regexp_b1, MethodThatRaisesRegexp)

self.assertRaisesRegexp(
    raises_regexp_a2, raises_regexp_b2,
    MethodThatRaisesRegexp,
    raises_regexp_c2, raises_regexp_d2)

with self.assertRaisesWithRegexpMatch(
    raises_with_regexp_match_a0, raises_with_regexp_match_b0):
  MethodThatRaisesRegexp()

self.assertRaisesWithRegexpMatch(
    raises_with_regexp_match_a1, raises_with_regexp_match_b1,
    MethodThatRaisesRegexp)

self.assertRaisesWithRegexpMatch(
    raises_with_regexp_match_a2, raises_with_regexp_match_b2,
    MethodThatRaisesRegexp,
    raises_with_regexp_match_c2, raises_with_regexp_match_d2)

# pylint: enable=bad-continuation
# pylint: enable=line-too-long
# pylint: enable=undefined-variable
