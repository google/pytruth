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

AssertThat(equal_a0).IsEqualTo(equal_b0)
AssertThat(equal_t0).IsTrue()
AssertThat(equal_f0).IsFalse()
AssertThat(equal_n0).IsNone()
AssertThat(equal_n1).IsEqualTo(26)
AssertThat(equal_n2).IsEqualTo(27)
AssertThat(equal_n3).IsEqualTo(2.8)
AssertThat(equal_n4).IsEqualTo(-29)
AssertThat(equal_n5).IsEqualTo(30L)
AssertThat(equal_n6).IsEqualTo(-3.1)
AssertThat(equal_z0).IsZero()
AssertThat(equal_z1).IsZero()
AssertThat(function_call()).IsEqualTo(equal_m0)

AssertThat(equal_long_method(arg0, (tuple_e0, tuple_e1),
                                   [list(list_e0, list_e1)])).IsEqualTo(equal_long_method({dict_k0: dict_v0,
                                    dict_k1: (tuple_e0, tuple_e1)}))

AssertThat(equal_ra0).IsEqualTo('equal_rb0')
AssertThat(equal_ra1).IsEqualTo('equal_rb1')
AssertThat(equal_ra2).IsEqualTo("equal_rb2")
AssertThat(equal_ra3).IsEqualTo("equal_rb3")
AssertThat(actual_ra4).IsEqualTo(equal_rb4)
AssertThat(actual_ra5).IsEqualTo(equal_rb5)
AssertThat(equal_ra6).IsEqualTo(expected_rb6)
AssertThat(equal_ra7).IsEqualTo(expected_rb7)
AssertThat(result_ra8).IsEqualTo(equal_rb8)
AssertThat(result_ra9).IsEqualTo(equal_rb9)
AssertThat(os.environ['ENV0']).IsEqualTo(equal_rba)
AssertThat(os.environ['ENV1']).IsEqualTo(equal_rbb)
AssertThat(os.environ.get('ENV2')).IsEqualTo(equal_rbc)
AssertThat(os.environ.get('ENV3')).IsEqualTo(equal_rbd)
AssertThat(equal_rae).HasSize(55)
AssertThat(equal_raf).HasSize(56)
AssertThat(equal_rag).IsEmpty()
AssertThat(equal_rah).IsEmpty()

AssertThat(equal_e0).IsEmpty()
AssertThat(equal_e1).IsEmpty()
AssertThat(equal_e2).IsEmpty()
AssertThat(equal_e3).IsEmpty()
AssertThat(equal_e4).IsEmpty()
AssertThat(equal_e5).IsEmpty()
AssertThat(equal_e6).IsEmpty()
AssertThat(equal_e7).IsEmpty()
AssertThat(equal_e8).IsEmpty()
AssertThat(equal_e9).IsEmpty()
AssertThat(equal_ea).IsEmpty()
AssertThat(equal_eb).IsEmpty()
AssertThat(equal_ec).IsEmpty()
AssertThat(equal_ed).IsEmpty()
AssertThat(equal_ee).IsEmpty()
AssertThat(equal_ef).IsEmpty()
AssertThat(equal_eg).IsEmpty()
AssertThat(equal_eh).IsEmpty()
AssertThat(equal_ei).IsEmpty()
AssertThat(equal_ej).IsEmpty()
AssertThat(equal_ek).IsEmpty()
AssertThat(equal_el).IsEmpty()
AssertThat(equal_em).IsEmpty()
AssertThat(equal_en).IsEmpty()
AssertThat(equal_eo).IsEmpty()
AssertThat(equal_ep).IsEmpty()
AssertThat(equal_eq).IsEmpty()
AssertThat(equal_er).IsEmpty()

AssertThat(equal_l0).ContainsExactly(equal_b0, equal_c0).InOrder()
AssertThat(equal_l1).ContainsExactly(equal_b1, equal_c1).InOrder()
AssertThat(equal_l2).ContainsExactly(equal_b2, equal_c2).InOrder()
AssertThat(equal_l3).ContainsExactly(equal_b3, equal_c3).InOrder()
AssertThat(equal_l4).ContainsExactlyElementsIn(equal_b4 for equal_c4 in equal_d4).InOrder()
AssertThat(equal_l5).ContainsExactlyElementsIn(equal_b5 for equal_c5 in equal_d5).InOrder()
AssertThat(equal_l6).ContainsExactlyElementsIn(equal_b6 for equal_c6 in equal_d6)
AssertThat(equal_l7).ContainsExactly(equal_b7)
AssertThat(equal_l8).ContainsExactlyElementsIn(equal_b8 for equal_c8 in equal_d8).InOrder()
AssertThat(equal_l9).ContainsExactlyElementsIn(equal_b9 for equal_c9 in equal_d9).InOrder()
AssertThat(equal_la).ContainsExactlyElementsIn(equal_ba for equal_ca in equal_da)
AssertThat(equal_lb).ContainsExactly(equal_bb)

AssertThat(dict_subset_a0.items()).ContainsAllIn(dict_subset_b0.items())

AssertThat(dict_equal_a0).ContainsExactlyItemsIn(dict_equal_b0)
AssertThat(dict_equal_e0).IsEmpty()
AssertThat(dict_equal_e1).IsEmpty()
AssertThat(dict_equal_e2).IsEmpty()
AssertThat(dict_equal_e3).IsEmpty()
AssertThat(dict_equal_e4).IsEmpty()
AssertThat(dict_equal_e5).IsEmpty()
AssertThat(dict_equal_a6).ContainsExactlyItemsIn({dict_equal_b6: dict_equal_c6})
AssertThat(dict_equal_a7).ContainsExactlyItemsIn({dict_equal_b7: dict_equal_c7})

AssertThat(sorted(count_equal_a0)).ContainsExactlyElementsIn(sorted(count_equal_b0)).InOrder()
AssertThat(sorted(count_equal_a1)).ContainsExactlyElementsIn(sorted([count_equal_b1, count_equal_c1])).InOrder()
AssertThat(sorted(count_equal_a2)).ContainsExactlyElementsIn(sorted((count_equal_b2, count_equal_c2))).InOrder()
AssertThat(sorted(count_equal_a3)).ContainsExactlyElementsIn(sorted([count_equal_b3, count_equal_c3])).InOrder()
AssertThat(sorted(count_equal_a4)).ContainsExactlyElementsIn(sorted((count_equal_b4, count_equal_c4))).InOrder()
AssertThat(sorted(count_equal_a5)).ContainsExactlyElementsIn(sorted([count_equal_b5])).InOrder()

AssertThat(sorted(items_equal_a0)).ContainsExactlyElementsIn(sorted(items_equal_b0)).InOrder()
AssertThat(sorted(items_equal_a1)).ContainsExactlyElementsIn(sorted([items_equal_b1, items_equal_c1])).InOrder()
AssertThat(sorted(items_equal_a2)).ContainsExactlyElementsIn(sorted((items_equal_b2, items_equal_c2))).InOrder()
AssertThat(sorted(items_equal_a3)).ContainsExactlyElementsIn(sorted([items_equal_b3, items_equal_c3])).InOrder()
AssertThat(sorted(items_equal_a4)).ContainsExactlyElementsIn(sorted((items_equal_b4, items_equal_c4))).InOrder()
AssertThat(sorted(items_equal_a5)).ContainsExactlyElementsIn(sorted([items_equal_b5])).InOrder()

AssertThat(list_equal_a0).ContainsExactlyElementsIn(list_equal_b0).InOrder()
AssertThat(list_equal_l1).ContainsExactly(list_equal_b1, list_equal_c1).InOrder()
AssertThat(list_equal_l2).ContainsExactly(list_equal_b2, list_equal_c2).InOrder()
AssertThat(list_equal_l3).ContainsExactly(list_equal_b3)

AssertThat(sequence_equal_a0).ContainsExactlyElementsIn(sequence_equal_b0).InOrder()
AssertThat(sequence_equal_a1).ContainsExactly(sequence_equal_b1, sequence_equal_c1).InOrder()
AssertThat(sequence_equal_a2).ContainsExactly(sequence_equal_b2, sequence_equal_c2).InOrder()
AssertThat(sequence_equal_a3).ContainsExactly(sequence_equal_b3, sequence_equal_c3).InOrder()
AssertThat(sequence_equal_a4).ContainsExactly(sequence_equal_b4, sequence_equal_c4).InOrder()
AssertThat(sequence_equal_a5).ContainsExactly(sequence_equal_b5)

AssertThat(set_equal_a0).ContainsExactlyElementsIn(set_equal_b0)
AssertThat(set_equal_a1).ContainsExactly(set_equal_b1, set_equal_c1)
AssertThat(set_equal_a2).ContainsExactly(set_equal_b2, set_equal_c2)

AssertThat(tuple_equal_a0).ContainsExactlyElementsIn(tuple_equal_b0).InOrder()
AssertThat(tuple_equal_a1).ContainsExactly(tuple_equal_b1, tuple_equal_c1).InOrder()
AssertThat(tuple_equal_a2).ContainsExactly(tuple_equal_b2, tuple_equal_c2).InOrder()

AssertThat(same_elements_a0).ContainsExactlyElementsIn(same_elements_b0)
AssertThat(same_elements_a1).ContainsExactly(same_elements_b1, same_elements_c1)
AssertThat(same_elements_a2).ContainsExactly(same_elements_b2, same_elements_c2)
AssertThat(same_elements_a3).ContainsExactly(same_elements_b3, same_elements_c3)
AssertThat(same_elements_a4).ContainsExactly(same_elements_b4, same_elements_c4)
AssertThat(same_elements_a5).ContainsExactly(same_elements_b5)

AssertThat(equal_a1).IsEqualTo(equal_b1)

AssertThat(not_equal_a0).IsNotEqualTo(not_equal_b0)
AssertThat(not_equal_a1).IsNotEqualTo(not_equal_b1)
AssertThat(not_equal_t0).IsFalse()
AssertThat(not_equal_f0).IsTrue()
AssertThat(not_equal_n0).IsNotNone()
AssertThat(not_equal_n1).IsNotEqualTo(138)
AssertThat(not_equal_n2).IsNotEqualTo(139)
AssertThat(not_equal_n3).IsNotEqualTo(14.0)
AssertThat(not_equal_n4).IsNotEqualTo(-141)
AssertThat(not_equal_n5).IsNotEqualTo(142L)
AssertThat(not_equal_n6).IsNotEqualTo(-14.3)
AssertThat(not_equal_z0).IsNonZero()
AssertThat(not_equal_z1).IsNonZero()
AssertThat(function_call()).IsNotEqualTo(not_equal_m0)

AssertThat(not_equal_ra0).IsNotEqualTo('not_equal_rb0')
AssertThat(not_equal_ra1).IsNotEqualTo('not_equal_rb1')
AssertThat(not_equal_ra2).IsNotEqualTo("not_equal_rb2")
AssertThat(not_equal_ra3).IsNotEqualTo("not_equal_rb3")
AssertThat(actual_ra4).IsNotEqualTo(not_equal_rb4)
AssertThat(actual_ra5).IsNotEqualTo(not_equal_rb5)
AssertThat(not_equal_ra6).IsNotEqualTo(expected_rb6)
AssertThat(not_equal_ra7).IsNotEqualTo(expected_rb7)
AssertThat(result_ra8).IsNotEqualTo(not_equal_rb8)
AssertThat(result_ra9).IsNotEqualTo(not_equal_rb9)
AssertThat(os.environ['ENV0']).IsNotEqualTo(not_equal_rba)
AssertThat(os.environ['ENV1']).IsNotEqualTo(not_equal_rbb)
AssertThat(os.environ.get('ENV2')).IsNotEqualTo(not_equal_rbc)
AssertThat(os.environ.get('ENV3')).IsNotEqualTo(not_equal_rbd)
AssertThat(len(not_equal_rae)).IsNotEqualTo(162)
AssertThat(len(not_equal_raf)).IsNotEqualTo(163)
AssertThat(not_equal_rag).IsNotEmpty()
AssertThat(not_equal_rah).IsNotEmpty()

AssertThat(not_equal_e0).IsNotEmpty()
AssertThat(not_equal_e1).IsNotEmpty()
AssertThat(not_equal_e2).IsNotEmpty()
AssertThat(not_equal_e3).IsNotEmpty()
AssertThat(not_equal_e4).IsNotEmpty()
AssertThat(not_equal_e5).IsNotEmpty()
AssertThat(not_equal_e6).IsNotEmpty()
AssertThat(not_equal_e7).IsNotEmpty()
AssertThat(not_equal_e8).IsNotEmpty()
AssertThat(not_equal_e9).IsNotEmpty()
AssertThat(not_equal_ea).IsNotEmpty()
AssertThat(not_equal_eb).IsNotEmpty()
AssertThat(not_equal_ec).IsNotEmpty()
AssertThat(not_equal_ed).IsNotEmpty()
AssertThat(not_equal_ee).IsNotEmpty()
AssertThat(not_equal_ef).IsNotEmpty()
AssertThat(not_equal_eg).IsNotEmpty()
AssertThat(not_equal_eh).IsNotEmpty()
AssertThat(not_equal_ei).IsNotEmpty()
AssertThat(not_equal_ej).IsNotEmpty()
AssertThat(not_equal_ek).IsNotEmpty()
AssertThat(not_equal_el).IsNotEmpty()
AssertThat(not_equal_em).IsNotEmpty()
AssertThat(not_equal_en).IsNotEmpty()
AssertThat(not_equal_eo).IsNotEmpty()
AssertThat(not_equal_ep).IsNotEmpty()
AssertThat(not_equal_eq).IsNotEmpty()
AssertThat(not_equal_er).IsNotEmpty()

AssertThat(underscore).IsTrue()

AssertThat(true_a0).IsTrue()

AssertThat(false_a0).IsFalse()

AssertThat(less_a0).IsLessThan(less_b0)
AssertThat(less_a1).IsLessThan(203)
AssertThat(less_a2).IsGreaterThan(204)

AssertThat(less_equal_a0).IsAtMost(less_equal_b0)
AssertThat(less_equal_a1).IsAtMost(207)
AssertThat(less_equal_a2).IsAtLeast(208)

AssertThat(greater_a0).IsGreaterThan(greater_b0)
AssertThat(greater_a1).IsGreaterThan(211)
AssertThat(greater_a2).IsLessThan(212)

AssertThat(greater_equal_a0).IsAtLeast(greater_equal_b0)
AssertThat(greater_equal_a1).IsAtLeast(215)
AssertThat(greater_equal_a2).IsAtMost(216)

AssertThat(is_a0).IsSameAs(is_b0)

AssertThat(is_not_a0).IsNotSameAs(is_not_b0)

AssertThat(is_none_a0).IsNone()

AssertThat(is_not_none_a0).IsNotNone()

AssertThat(is_instance_a0).IsInstanceOf(is_instance_b0)

AssertThat(is_not_instance_a0).IsNotInstanceOf(is_not_instance_b0)

AssertThat(in_a0).IsIn(in_b0)
AssertThat(in_a1).IsAnyOf(in_b1, in_c1)
AssertThat(in_a2).IsAnyOf(in_b2, in_c2)

AssertThat(not_in_a0).IsNotIn(not_in_b0)
AssertThat(not_in_a1).IsNoneOf(not_in_b1, not_in_c1)
AssertThat(not_in_a2).IsNoneOf(not_in_b2, not_in_c2)

AssertThat(starts_a0).StartsWith('starts_b0')
AssertThat(starts_a1).StartsWith("starts_b1")
AssertThat(starts_a2).StartsWith(r'starts_b2')
AssertThat(starts_a3).StartsWith(u"starts_b3")
AssertThat(starts_a4).StartsWith(r"starts_b4")
AssertThat(starts_a5).StartsWith(u'starts_b5')

AssertThat(ends_a0).EndsWith('ends_b0')
AssertThat(ends_a1).EndsWith("ends_b1")
AssertThat(ends_a2).EndsWith(r'ends_b2')
AssertThat(ends_a3).EndsWith(u"ends_b3")
AssertThat(ends_a4).EndsWith(r"ends_b4")
AssertThat(ends_a5).EndsWith(u'ends_b5')

AssertThat(regex_a0).ContainsMatch(regex_b0)

AssertThat(regexp_matches_a0).ContainsMatch(regexp_matches_b0)

AssertThat(not_regex_a0).DoesNotContainMatch(not_regex_b0)

AssertThat(not_regexp_matches_a0).DoesNotContainMatch(not_regexp_matches_b0)

with AssertThat(raises_a0).IsRaised():
  MethodThatRaises()

with AssertThat(raises_a1).IsRaised():
  MethodThatRaises()

with AssertThat(raises_a2).IsRaised():
  MethodThatRaises(raises_b2, raises_c2)

with AssertThat(raises_regexp_a0).IsRaised(matching=raises_regexp_b0):
  MethodThatRaisesRegexp()

with AssertThat(raises_regexp_a1).IsRaised(matching=raises_regexp_b1):
  MethodThatRaisesRegexp()

with AssertThat(raises_regexp_a2).IsRaised(matching=raises_regexp_b2):
  MethodThatRaisesRegexp(raises_regexp_c2, raises_regexp_d2)

with AssertThat(raises_with_regexp_match_a0).IsRaised(matching=raises_with_regexp_match_b0):
  MethodThatRaisesRegexp()

with AssertThat(raises_with_regexp_match_a1).IsRaised(matching=raises_with_regexp_match_b1):
  MethodThatRaisesRegexp()

with AssertThat(raises_with_regexp_match_a2).IsRaised(matching=raises_with_regexp_match_b2):
  MethodThatRaisesRegexp(raises_with_regexp_match_c2, raises_with_regexp_match_d2)

# pylint: enable=bad-continuation
# pylint: enable=line-too-long
# pylint: enable=undefined-variable
